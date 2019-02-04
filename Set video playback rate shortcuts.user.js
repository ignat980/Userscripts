// ==UserScript==
// @name         Set video playback rate shortcuts
// @namespace    http://ignat.space/
// @version      4.1
// @description  Set every video's playback rate to 1 by pressing 'y', 2 by douple-tapping 'y', 3 by tapping 'u', 3.5 by double-tapping 'y', 1.5 by tapping 'y' then 'u', and 2.5 by tapping 'u' then 'y'.
// @author       Ignat Remizov
// @match        *://*/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
    console.log("Running script on", document);
    function setVideoSpeed(speed) {
        for (let video of document.getElementsByTagName('video')){
            //console.log("Setting speed to " + speed + " on", video);
            video.playbackRate = speed;
        }
    }
    var lastPressed;
    var prevTimeStamp = 0;
    var [keyI, keyU, keyY] = [73, 85, 89];
    window.addEventListener("keydown", function(e) {
        //If writing something in a text field (like a comment or a search), don't trigger a speed change
        if (e.target.nodeName == "TEXTAREA" || e.target.nodeName == "INPUT" || e.target.nodeName == "YT-FORMATTED-STRING") return;
        var key = e.keyCode ? e.keyCode : e.which;
        var duration = e.timeStamp - prevTimeStamp;
        if (key === keyU) {
            if (lastPressed === keyU && (duration < 300)) {
                setVideoSpeed(3.5);
            } else if (lastPressed === keyY && (duration < 300)){
                setVideoSpeed(1.5);
            } else {
                setVideoSpeed(3);
            }
        } else if (key === keyY) {
            if (lastPressed === keyY && (duration < 300)) {
                setVideoSpeed(2);
            } else if (lastPressed === keyU && (duration < 300)){
                setVideoSpeed(2.5);
            } else {
                setVideoSpeed(1);
            }
        }
        lastPressed = key;
        prevTimeStamp = e.timeStamp;
    });
})();