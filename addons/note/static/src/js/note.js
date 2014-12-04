odoo.define("note.note", function(require) {
'use strict';

var core = require('web.core');
var kanban_common = require('web_kanban.common');

var _t = core._t;

kanban_common.KanbanGroup.include({
    init: function() {
        this._super.apply(this, arguments);
        this.title = ((this.dataset.model === 'note.note') && (this.title === _t('Undefined'))) ? _t('Shared') : this.title;
    },
});

});