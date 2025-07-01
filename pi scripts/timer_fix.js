// ==UserScript==
// @name         Fix TVHeadend Issue
// @namespace    http://tampermonkey.net/
// @version      2025-06-29
// @description  Replace occurrences of `RegExp.escape(r.get(this.valueField))` with `RegExp.escape(String(r.get(this.valueField)))`.
// @author       Klurdy Studios
// @match        http://172.22.2.103:9981/*
// @grant        none
// ==/UserScript==

// https://tvheadend.org/d/9019-cannot-open-addedit-autorec-dialog-in-firefox/4

(function() {
    'use strict';

    // Function to intercept and modify scripts before they execute
    const interceptAndModifyScripts = () => {
        // Get all script elements
        const scriptElements = document.querySelectorAll('script');

        // Process each script element
        scriptElements.forEach(script => {
            if (script.textContent && script.textContent.includes('RegExp.escape(r.get(this.valueField))')) {
                // Replace the target code with the fixed version
                const modifiedContent = script.textContent.replace(
                    /RegExp\.escape\(r\.get\(this\.valueField\)\)/g,
                    'RegExp.escape(String(r.get(this.valueField)))'
                );

                // Create a new script element with the modified content
                const newScript = document.createElement('script');
                newScript.textContent = modifiedContent;

                // Replace the original script with the new one
                script.parentNode.replaceChild(newScript, script);
            }
        });
    };

    // Create a MutationObserver to watch for dynamically added scripts
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.addedNodes) {
                mutation.addedNodes.forEach((node) => {
                    // Check if the added node is a script element
                    if (node.tagName === 'SCRIPT' && node.textContent &&
                        node.textContent.includes('RegExp.escape(r.get(this.valueField))')) {

                        // Prevent the script from executing
                        node.stop();

                        // Replace the target code with the fixed version
                        const modifiedContent = node.textContent.replace(
                            /RegExp\.escape\(r\.get\(this\.valueField\)\)/g,
                            'RegExp.escape(String(r.get(this.valueField)))'
                        );

                        // Create a new script element with the modified content
                        const newScript = document.createElement('script');
                        newScript.textContent = modifiedContent;

                        // Replace the original script with the new one
                        node.parentNode.replaceChild(newScript, node);
                    }
                });
            }
        });
    });

    // Alternative method using script injection for already loaded scripts
    const injectFix = () => {
        const script = document.createElement('script');
        script.textContent = `
            // Store the original RegExp.escape function
            const originalRegExpEscape = RegExp.escape;

            // Override RegExp.escape to handle non-string inputs
            RegExp.escape = function(input) {
                return originalRegExpEscape(String(input));
            };

            console.log("[Tampermonkey] RegExp.escape patched to handle non-string inputs");
        `;
        document.head.appendChild(script);
    };

    // Run initial script modification
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            interceptAndModifyScripts();
            injectFix();
        });
    } else {
        interceptAndModifyScripts();
        injectFix();
    }

    // Start observing the document for dynamically added scripts
    observer.observe(document, { childList: true, subtree: true });

    console.log("[Tampermonkey] Script fix for RegExp.escape TypeError installed");
})();