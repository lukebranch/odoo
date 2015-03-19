(function () {
    'use strict';

    if (!openerp.website.translatable) {
        // Temporary hack until the editor bar is moved to the web client
        return;
    }

    (function($) {
        $.fn.bindFirst = function(/*String*/ eventType, /*[Object])*/ eventData, /*Function*/ handler) {
            var indexOfDot = eventType.indexOf(".");
            var eventNameSpace = indexOfDot > 0 ? eventType.substring(indexOfDot) : "";

            eventType = indexOfDot > 0 ? eventType.substring(0, indexOfDot) : eventType;
            handler = handler == undefined ? eventData : handler;
            eventData = typeof eventData == "function" ? {} : eventData;

            return this.each(function() {
                var $this = $(this);
                var currentAttrListener = this["on" + eventType];

                if (currentAttrListener) {
                    $this.bind(eventType, function(e) {
                        return currentAttrListener(e.originalEvent);
                    });

                    this["on" + eventType] = null;
                }

                $this.bind(eventType + eventNameSpace, eventData, handler);

                var allEvents = $this.data("events") || $._data($this[0], "events");
                var typeEvents = allEvents[eventType];
                var newEvent = typeEvents.pop();
                typeEvents.unshift(newEvent);
            });
        };
    })(jQuery);


    var website = openerp.website;
    var web_editor = openerp.web_editor;

    web_editor.Translate = openerp.Widget.extend({
        do_not_translate : ['-','*','!'],
        init: function (parent, $target, model, id, field, lang) {
            this.parent = parent;

            this.setTarget($target);

            this.model = model;
            this.id = id;
            this.field = field;
            this.lang = lang || web_editor.get_context().lang;

            this.initial_content = {};

            this._super();
        },
        setTarget: function ($target) {
            this.$target = $target
                .not('link, script')
                .filter('[data-oe-field=arch], [data-oe-type][data-oe-translate!=0]');
        },
        find: function (selector) {
            return selector ? this.$target.find(selector).addBack().filter(selector) : this.$target;
        },
        edit: function () {
            return this.translate().then(_.bind(this.onTranslateReady, this));
        },
        translate: function () {
            var self = this;
            this.translations = null;
            return openerp.jsonRpc('/website/get_view_translations', 'call', {
                'xml_id': this.id,
                'lang': this.lang,
            }).then(function (translations) {
                self.translations = translations;
                self.processTranslatableNodes();
            });
        },
        onTranslateReady: function () {
            this.trigger("edit");
        },
        processTranslatableNodes: function () {
            var self = this;
            this.$target.each(function () {
                var $node = $(this);
                var $object = $node.closest('[data-oe-id]');
                var view_id = $object.attr('data-oe-source-id') || $object.attr('data-oe-id') | 0;
                self.transNode(this, view_id);
            });
            this.find('.o_translatable_text').on('paste', function () {
                var node = $(this);
                setTimeout(function () {
                    self.sanitizeNode(node);
                }, 0);
            });
            $(document).on('keyup paste', '.o_translatable_text, .o_translatable_field', function(ev) {
                var $node = $(this);
                setTimeout(function () {
                    // Doing stuff next tick because paste and keyup events are
                    // fired before the content is changed
                    if (ev.type == 'paste') {
                        self.sanitizeNode($node[0]);
                    }

                    var $nodes = $node;
                    if ($node.attr('data-oe-nodeid')) {
                        $nodes = $nodes.add(self.find('[data-oe-nodeid=' + $node.attr('data-oe-nodeid') + ']').each(function () {
                            if ($node[0] !== this) self.setText(this, $node.text());
                        }));
                    }

                    if (self.getInitialContent($node[0]) !== $node.text().trim()) {
                        $nodes.addClass('o_dirty');
                        if ($node.hasClass('o_translatable_todo_r')) {
                            $nodes.removeClass('o_translatable_todo').addClass('o_translatable_todo_r');
                        }
                        if ($node.hasClass('o_translatable_inprogress_r')) {
                            $nodes.removeClass('o_translatable_inprogress').addClass('o_translatable_inprogress_r');
                        }
                    } else {
                        $nodes.removeClass('o_dirty');
                        if ($node.hasClass('o_translatable_todo_r')) {
                            $nodes.addClass('o_translatable_todo').removeClass('o_translatable_todo_r');
                        }
                        if ($node.hasClass('o_translatable_inprogress_r')) {
                            $nodes.addClass('o_translatable_inprogress').removeClass('o_translatable_inprogress_r');
                        }
                    }
                }, 0);
            });
        },
        getInitialContent: function (node) {
            return this.initial_content[node.getAttribute('data-oe-nodeid')];
        },
        sanitizeNode: function (node) {
            node.text(node.text());
        },
        isTextNode: function (node) {
            return node.nodeType === 3 || node.nodeType === 4;
        },
        isTranslatable: function (text) {
            return text && _.str.trim(text) !== '';
        },
        setText: function (node, text) {
            node.textContent = node.getAttribute('data-oe-translate-space-before') + _.str.trim(text) + node.getAttribute('data-oe-translate-space-after');
        },
        transNode: function (node, view_id) {
            if (node.childNodes.length === 1
                    && this.isTextNode(node.childNodes[0])
                    && !node.getAttribute('data-oe-model')) {
                this.markTranslatableNode(node, view_id);
            } else {
                for (var i = 0, l = node.childNodes.length; i < l; i ++) {
                    var n = node.childNodes[i];
                    if (this.isTextNode(n)) {
                        if (this.isTranslatable(n.data)) {
                            var container = document.createElement('span');
                            container.className = "o_translatable_ghost_node";
                            node.insertBefore(container, n);
                            container.appendChild(n);
                            this.markTranslatableNode(container, view_id);
                        }
                    } else {
                        this.transNode(n, view_id);
                    }
                }
            }

            this.$target.bindFirst('click', this._cancelClick);
        },
        _cancelClick: function (event) {
            event.preventDefault();
            event.stopPropagation();
        },
        markTranslatableNode: function (node, view_id) {
            var is_field = !!$(node).closest("[data-oe-type]").length;
            var content = node.childNodes[0].data.trim();
            var nid = _.findKey(this.initial_content, function (v, k) { return v === content;});

            if (!is_field) {
                node.className += ' o_translatable_text';
                node.setAttribute('data-oe-translation-view-id', view_id);

                var trans = this.translations.filter(function (t) {
                    return t.res_id === view_id && t.value.trim() === content;
                });
                if (trans.length) {
                    node.setAttribute('data-oe-translation-id', trans[0].id);
                    if(trans[0].state && (trans[0].state == 'inprogress' || trans[0].state == 'to_translate')){
                        node.className += ' o_translatable_inprogress';
                    }
                } else {
                    node.className += this.do_not_translate.indexOf(node.textContent.trim()) ? ' o_translatable_todo' : '';
                }
            } else {
                node.className += ' o_translatable_field';
            }

            nid = nid || _.uniqueId();
            node.setAttribute('data-oe-nodeid', nid);
            node.setAttribute('contentEditable', true);
            var space = node.textContent.match(/^([\s]*)[\s\S]*?([\s]*)$/);
            node.setAttribute('data-oe-translate-space-before', space[1] || '');
            node.setAttribute('data-oe-translate-space-after', space[2] || '');

            this.initial_content[nid] = content;
        },
        save: function () {
            var self = this;
            var keys = {};
            var trans = {};
            this.find('.o_translatable_text.o_dirty').each(function () {
                var content = self.getInitialContent(this);
                if (keys[content]) return;
                keys[content] = true;

                var oeTranslationViewId = this.getAttribute('data-oe-translation-view-id');
                if (!trans[oeTranslationViewId]) {
                    trans[oeTranslationViewId] = [];
                }
                trans[oeTranslationViewId].push({
                    'initial_content':  content,
                    'new_content':      _.str.trim($(this).text()),
                    'translation_id':   (this.getAttribute('data-oe-translation-id') | 0) || null
                });
            });

            var field_trans = [];
            this.find('.o_translatable_field.o_dirty').each(function () {
                var $node = $(this).closest("[data-oe-type]");

                var content = self.getInitialContent(this);
                if (keys[content]) return;
                keys[content] = true;

                field_trans.push({
                    'initial_content':  content,
                    'new_content':  _.str.trim($(this).text()),
                    'model':        $node.attr('data-oe-model') || null,
                    'id':           ($node.attr('data-oe-id') | 0) || null,
                    'field':        $node.attr('data-oe-field') || null,
                });
            });
            
            console.log("TO DO translate for t-field and for html field");
            console.log(field_trans);

            return openerp.jsonRpc('/website/set_translations', 'call', {
                'data': trans,
                'lang': this.lang,
            }).then(function () {
                self.unarkTranslatableNode();
                self.trigger("saved");
            }).fail(function () {
                // TODO: bootstrap alert with error message
                alert("Could not save translation");
            });
        },
        unarkTranslatableNode: function () {
            this.find('.o_translatable_ghost_node').each(function () {
                this.parentNode.insertBefore(this.firstChild, this);
                this.parentNode.removeChild(this);
            });

            this.find('.o_translatable_text, .o_translatable_field')
                .removeClass('o_translatable_text o_translatable_todo o_translatable_inprogress o_translatable_field o_dirty')
                .removeAttr('data-oe-nodeid')
                .removeAttr('data-oe-translation-id')
                .removeAttr('data-oe-translation-view-id')
                .removeAttr('data-oe-translation-space-before')
                .removeAttr('data-oe-translation-space-after')
                .removeAttr('contentEditable')
                .each(function () {
                    if (!this.className.match(/\S/)) {
                        this.removeAttribute("class");
                    }
                });

            this.$target.off('click', this._cancelClick);
        },
        cancel: function () {
            var self = this;
            this.find('.o_translatable_text').each(function () {
                self.setText(this, self.getInitialContent(this));
            });
            this.unarkTranslatableNode();
            this.trigger("cancel");
        },
        destroy: function () {
            this.cancel();
            this._super();
        }
    });


    web_editor.add_template_file('/website/static/src/xml/website.translator.xml');
    var nodialog = 'website_translator_nodialog';


    website.Translate = web_editor.Translate.extend({
        events: {
            'click [data-action="save"]': 'save',
            'click [data-action="cancel"]': 'cancel',
        },
        template: 'website.translator',
        onTranslateReady: function () {
            if(this.gengo_translate){
                this.translation_gengo_display();
            }
            this._super();
        },
        destroy: function () {
            this.$el.remove();
            this._super();
        }
    });

    website.TranslatorDialog = openerp.Widget.extend({
        events: _.extend({}, website.TopBar.prototype.events, {
            'hidden.bs.modal': 'destroy',
            'click button[data-action=activate]': function (ev) {
                this.trigger('activate');
            },
        }),
        template: 'website.TranslatorDialog',
        start: function () {
            this.$el.modal();
        },
    });

    website.TopBar.include({
        events: _.extend({}, website.TopBar.prototype.events, {
            'click [data-action="edit_master"]': 'edit_master',
            'click [data-action="translate"]': 'translate',
        }),
        start: function () {
            var self = this;
            var res = this._super();
            var $edit_button = this.$("button[data-action=edit]");
            $edit_button.removeClass("hidden");

            if(website.no_editor) {
                $edit_button.removeProp('disabled');
            } else {
                $edit_button.attr("data-action", "translate");
                $edit_button.parent().after(openerp.qweb.render('website.TranslatorAdditionalButtons'));
            }

            $('.js_hide_on_translate').hide();
            return res;
        },
        translate: function () {
            var self = this;

            if (!localStorage[nodialog]) {
                var dialog = new website.TranslatorDialog();
                dialog.appendTo($(document.body));
                dialog.on('activate', this, function () {
                    localStorage[nodialog] = dialog.$('input[name=do_not_show]').prop('checked') || '';
                    dialog.$el.modal('hide');

                    self.on_translate();
                });
            } else {
                this.on_translate();
            }
        },
        on_translate: function () {
            var $editables = $('#wrapwrap [data-oe-model="ir.ui.view"], [data-oe-translate="1"]')
                    .not('link, script')
                    .not('#oe_snippets, #oe_snippets *, .navbar-toggle');

            if (!this.translator) {
                this.translator = new website.Translate(this, $editables, 'ir.ui.view', $(document.documentElement).data('view-xmlid'), 'arch');
                this.translator.on('saved cancel', this, this.stop_translate);
                this.translator.prependTo(document.body);
            } else {
                this.translator.setTarget($editables);
                this.translator.$el.show();
            }

            this.translator.edit();

            this.$('button[data-action=edit]').prop('disabled', true);
            this.$el.hide();
        },
        stop_translate: function () {
            this.translator.$el.hide();
            this.$('button[data-action=edit]').prop('disabled', false);
            this.$el.show();
        },
        edit_master: function (ev) {
            ev.preventDefault();
            var link = $('.js_language_selector a[data-default-lang]')[0];
            if (link) {
                link.search += (link.search ? '&' : '?') + 'enable_editor=1';
                window.location = link.attributes.href.value;
            }
        },
    });

})();
