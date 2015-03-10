odoo.define('website_forum.editor', ['web.core', 'website.contentMenu', 'website.website'], function (require) {
"use strict";

var core = require('web.core');
var contentMenu = require('website.contentMenu');
var website = require('website.website');

var _t = core._t;

contentMenu.EditorBarContent.include({
    new_forum: function() {
        website.prompt({
            id: "editor_new_forum",
            window_title: _t("New Forum"),
            input: "Forum Name",
        }).then(function (forum_name) {
            website.form('/forum/new', 'POST', {
                forum_name: forum_name
            });
        });
    },
});

});
