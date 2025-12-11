/*
This is an example startup file. You can load it from your startup file
(to be found in Platform.userAppSupportDir +/+ "startup.scd")
*/

(
s.reboot { // server options are only updated on reboot
    // configure the sound server: here you could add hardware specific options
    // see http://doc.sccode.org/Classes/ServerOptions.html
    s.options.numBuffers = 1024 * 256; // increase this if you need to load more samples
    s.options.memSize = 8192 * 32; // increase this if you get "alloc failed" messages
    s.options.numWireBufs = 128; // increase this if you get "exceeded number of interconnect buffers" messages
    s.options.maxNodes = 1024 * 32; // increase this if you are getting drop outs and the message "too many nodes"
    s.options.numOutputBusChannels = 2; // set this to your hardware output channel size, if necessary
	/* Input setup fails: "get kAudioDevicePropertyStreamFormat error on input ?ohw" */
    s.options.numInputBusChannels = 0; // set this to your hardware input channel size, if necessary
	// s.options.device = "MacBook Air Speakers";

	// remove any previous defs if they exist
	{ OSCdef(\gpStartRecord).free }.try;
	{ OSCdef(\gpStopRecord).free }.try;

    // boot the server and start SuperDirt
    s.waitForBoot {
		~dirt.stop; // stop any old ones, avoid duplicate dirt (if it is nil, this won't do anything)
        ~dirt = SuperDirt(2, s); // two output channels, increase if you want to pan across more channels
        ~dirt.loadSoundFiles;   // load samples (path containing a wildcard can be passed in)
        // for example: ~dirt.loadSoundFiles("/Users/myUserName/Dirt/samples/*");
		SuperDirt.default = ~dirt; // make this instance available in sclang (optional)
        s.sync; // optionally: wait for samples to be read
		/* This reserves a muted orbit. It's useful for actual operation */
		// ~dirt.start(57120, [0, 0, 0, 0, 0, 0, 0, 0, 8]); // Route orbit 8 to missing (muted) channel 8
		/* Activate all channels and do not mute any */
		~dirt.start(57120, Array.fill(12, 0));  // ✅ ALL orbits audible
		"SuperDirt started and ready!".postln;


		// ~dirt.start(57120, 0 ! 12);   // start listening on port 57120, create two busses each sending audio to channel 0
        // optional, needed for convenient access from sclang:
        /*(
            ~d1 = ~dirt.orbits[0]; ~d2 = ~dirt.orbits[1]; ~d3 = ~dirt.orbits[2];
            ~d4 = ~dirt.orbits[3]; ~d5 = ~dirt.orbits[4]; ~d6 = ~dirt.orbits[5];
            ~d7 = ~dirt.orbits[6]; ~d8 = ~dirt.orbits[7]; ~d9 = ~dirt.orbits[8];
            ~d10 = ~dirt.orbits[9]; ~d11 = ~dirt.orbits[10]; ~d12 = ~dirt.orbits[11];
        );*/

		~gp_rec_synth = nil;
        ~gp_rec_buf   = nil;
        ~gp_record_path = nil;

        // SynthDef: record stereo bus (0..1) directly to disk via DiskOut
		// === Recording SynthDef ===
		SynthDef(\gpDiskOut, { |bufnum, out=0|
			var sig = In.ar(out, 2);
			DiskOut.ar(bufnum, sig);
		}).add;

		// ---- /gp/startRecord ----
		OSCdef(\gpStartRecord, { |msg|
			{
				var path, dur = 8.0;

				path = (msg.size >= 2).if({ msg[1].asString }, {
					Platform.userHomeDir +/+ "genetic_music/rec_" ++ Date.getDate.stamp ++ ".wav"
				});
				if (msg.size >= 3) { dur = msg[2].asFloat };

				if (path.beginsWith("/").not) {
					path = Platform.userHomeDir +/+ path;
				};

				// Ensure folder exists
				File.mkdir(PathName(path).pathOnly);

				// Stop any old recording
				s.stopRecording;

				// Start recording the main output (bus 0)
				s.record(path: path, bus: 0, numChannels: 2);
				~gp_record_path = path;

				("[SC] Recording started -> " ++ path ++ " for " ++ dur ++ "s").postln;

				// Automatically stop after duration
				SystemClock.sched(dur, {
					s.stopRecording;
					("[SC] Auto-stopped recording -> " ++ path).postln;
				});
			}.fork(AppClock);
		}, '/gp/startRecord');


		// ---- /gp/stopRecord ----
		OSCdef(\gpStopRecord, { |msg|
			{
				s.stopRecording;
				("[SC] Stopped recording manually. File -> " ++ (~gp_record_path ? "unknown")).postln;
			}.fork(AppClock);
		}, '/gp/stopRecord');

        "GP buffer recorder ready (abs-path + safe fork).".postln;
	};


    s.latency = 0.4; // increase this if you get "late" messages
};

// General trace
OSCFunc.trace(false);

// Listen specifically for /dirt/play messages
OSCdef(\dirtMonitor, { |msg, time, addr, port|
    "=== DIRT MESSAGE RECEIVED ===".postln;
    msg.postln;
    "=============================".postln;
}, '/dirt/play');


);
