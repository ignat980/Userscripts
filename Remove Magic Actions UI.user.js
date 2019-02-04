// ==UserScript==
// @name         Remove Magic Actions UI
// @namespace    http://ignat.space/
// @version      1.3
// @description  Removes a few pervasive UI Elements from the YouTube Chrome extension "Magic Actions"
// @author       Ignat Remizov
// @match        *://*.youtube.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';
    var config = {childList: true, subtree: true}; //observer config
    var observer = new MutationObserver(function(mutations) { //create observer looking at doc
      mutations.forEach(mutation => {
        if (mutation.target.tagName === "YTD-VIDEO-PRIMARY-INFO-RENDERER") { //if added element is yt video info (description, likes, etc.)
          console.log("Found yt info:", mutation.target, "Its child length is", mutation.target.children.length); //log it
          var p = mutation.target.children; //magic actions bar is always already loaded
          for (var child in p) {
            if (p[child].tagName === "SPAN" && p[child].className === "") {
              console.log('Removing',p[child]);
              p[child].remove(); //remove it
              document.getElementById("ym_eeb0").remove(); //also remove the lightswitch, id changes sometimes
              break;
            }
          }
        }
      });
    });
    observer.observe(document, config); //Start the observer
})();