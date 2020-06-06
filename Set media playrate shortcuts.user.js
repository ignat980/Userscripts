// ==UserScript==
// @name         Set media playrate shortcuts
// @namespace    http://ignat.space/
// @version      6.0
// @author       Ignat Remizov
// @description  Set every media element's playback rate. https://imgur.com/a/doFZXOI - visual explanation. Works for local mp4 files. Make sure "Run only in top frame:" setting is set to "No". Set to 1 by pressing 'y', 2 by douple-tapping 'y', 3 by tapping 'u', 3.5 by double-tapping 'y', 1.5 by tapping 'y' then 'u', and 2.5 by tapping 'u' then 'y'. Set to slower speeds by holding shift. You can also set media to loop by pressing 'p'.
// @match        *://*/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
    console.log("Running media playrate shortcuts script on", document); //Useful for debugging which iframe the script is running on
    //Config
    var [KEY_SLOW, KEY_FAST, KEY_LOOP] = [89, 85, 80]; //keys 'Y', 'U', and 'P' on a standard QWERTY keyboard - change with codes from https://keycode.info/ if you want (careful on YouTube, there are some keys that are already bound, check by pressing "shift+/" - "?")
    //Functions
    function setSpeed(speed) {
        for (let video of document.getElementsByTagName('video')) {
            //console.log("Setting speed to " + speed + " on", video);
            video.playbackRate = speed;
        }
        for (let audio of document.getElementsByTagName('audio')) {
            //console.log("Setting speed to " + speed + " on", audio);
            audio.playbackRate = speed;
        }
    }
    function setLoop(state) {
        for (let video of document.getElementsByTagName('video')) {
            video.loop = state;
        }
        for (let audio of document.getElementsByTagName('audio')) {
            audio.loop = state;
        }
    }
    var lastPressed;
    var prevTimeStamp = 0;
    window.addEventListener("keydown", function(e) {
        //If writing something in a text field (like a comment or a search), don't trigger a speed change
        if (e.target.nodeName == "TEXTAREA" || e.target.nodeName == "INPUT" || e.target.nodeName == "YT-FORMATTED-STRING" || e.target.id == "contenteditable-root") return;
        var key = e.keyCode ? e.keyCode : e.which;
        var duration = e.timeStamp - prevTimeStamp;
        var KEYPRESS_INTERVAL = 300;
        switch (key) {
            case KEY_SLOW: {
                if (e.shiftKey){
                    setSpeed(0.25)
                    break;
                }
                if (lastPressed === KEY_SLOW && (duration < KEYPRESS_INTERVAL)) {
                    setSpeed(2);
                } else if (lastPressed === KEY_FAST && (duration < KEYPRESS_INTERVAL)){
                    setSpeed(2.5);
                } else {
                    setSpeed(1);
                }
                break;
            }
            case KEY_FAST: {
                if (e.shiftKey){
                    setSpeed(0.5)
                    break;
                }
                if (lastPressed === KEY_FAST && (duration < KEYPRESS_INTERVAL)) {
                    setSpeed(3.5);
                } else if (lastPressed === KEY_SLOW && (duration < KEYPRESS_INTERVAL)){
                    setSpeed(1.5);
                } else {
                    setSpeed(3);
                }
                break;
            }
            case KEY_LOOP: {
                if (lastPressed === KEY_LOOP && (duration < KEYPRESS_INTERVAL)) {
                    setLoop(false);
                } else {
                    setLoop(true);
                }
                break;
            }
        }
        lastPressed = key;
        prevTimeStamp = e.timeStamp;
    });
})();