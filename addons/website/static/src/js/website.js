(function() {
    "use strict";

    /* --- Set the browser into the dom for css selectors --- */
    var browser;
    if ($.browser.webkit) browser = "webkit";
    else if ($.browser.safari) browser = "safari";
    else if ($.browser.opera) browser = "opera";
    else if ($.browser.msie || ($.browser.mozilla && +$.browser.version.replace(/^([0-9]+\.[0-9]+).*/, '\$1') < 20)) browser = "msie";
    else if ($.browser.mozilla) browser = "mozilla";
    browser += ","+$.browser.version;
    if (/android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(navigator.userAgent.toLowerCase())) browser += ",mobile";
    document.documentElement.setAttribute('data-browser', browser);
    /* ---------------------------------------------------- */

    var website = {};
    openerp.website = website;

    website.translatable = !!$('html').data('translatable');

    /* ----------------------------------------------------
       Helpers
       ---------------------------------------------------- */ 
    website.get_context = function (dict) {
        var html = document.documentElement;
        return _.extend({
            lang: html.getAttribute('lang').replace('-', '_'),
            website_id: html.getAttribute('data-website-id')|0
        }, dict);
    };

    website.parseQS = function (qs) {
        var match,
            params = {},
            pl     = /\+/g,  // Regex for replacing addition symbol with a space
            search = /([^&=]+)=?([^&]*)/g;

        while ((match = search.exec(qs))) {
            var name = decodeURIComponent(match[1].replace(pl, " "));
            var value = decodeURIComponent(match[2].replace(pl, " "));
            params[name] = value;
        }
        return params;
    };

    var parsedSearch;
    website.parseSearch = function () {
        if (!parsedSearch) {
            parsedSearch = website.parseQS(window.location.search.substring(1));
        }
        return parsedSearch;
    };

    website.parseHash = function () {
        return website.parseQS(window.location.hash.substring(1));
    };

    website.reload = function () {
        location.hash = "scrollTop=" + window.document.body.scrollTop;
        if (location.search.indexOf("enable_editor") > -1) {
            window.location.href = window.location.href.replace(/enable_editor(=[^&]*)?/g, '');
        } else {
            window.location.reload();
        }
    };

    /* ----------------------------------------------------
       Widgets
       ---------------------------------------------------- */ 

    website.error = function(data, url) {
        var def = $.Deferred().resolve();
        if (!('website.error_dialog' in openerp.qweb.templates)) {
            def = website.add_template_file('/website/static/src/xml/website.xml')
        }
        def.then(function(){
            var $error = $(openerp.qweb.render('website.error_dialog', {
                'title': data.data ? data.data.arguments[0] : "",
                'message': data.data ? data.data.arguments[1] : data.statusText,
                'backend_url': url
            }));
            $error.appendTo("body");
            $error.modal('show');
        });
    };

    website.form = function (url, method, params) {
        var form = document.createElement('form');
        form.setAttribute('action', url);
        form.setAttribute('method', method);
        _.each(params, function (v, k) {
            var param = document.createElement('input');
            param.setAttribute('type', 'hidden');
            param.setAttribute('name', k);
            param.setAttribute('value', v);
            form.appendChild(param);
        });
        document.body.appendChild(form);
        form.submit();
    };

    website.init_kanban = function ($kanban) {
        $('.js_kanban_col', $kanban).each(function () {
            var $col = $(this);
            var $pagination = $('.pagination', $col);
            if(!$pagination.size()) {
                return;
            }

            var page_count =  $col.data('page_count');
            var scope = $pagination.last().find("li").size()-2;
            var kanban_url_col = $pagination.find("li a:first").attr("href").replace(/[0-9]+$/, '');

            var data = {
                'domain': $col.data('domain'),
                'model': $col.data('model'),
                'template': $col.data('template'),
                'step': $col.data('step'),
                'orderby': $col.data('orderby')
            };

            $pagination.on('click', 'a', function (ev) {
                ev.preventDefault();
                var $a = $(ev.target);
                if($a.parent().hasClass('active')) {
                    return;
                }

                var page = +$a.attr("href").split(",").pop().split('-')[1];
                data['page'] = page;

                $.post('/website/kanban', data, function (col) {
                    $col.find("> .thumbnail").remove();
                    $pagination.last().before(col);
                });

                var page_start = page - parseInt(Math.floor((scope-1)/2), 10);
                if (page_start < 1 ) page_start = 1;
                var page_end = page_start + (scope-1);
                if (page_end > page_count ) page_end = page_count;

                if (page_end - page_start < scope) {
                    page_start = page_end - scope > 0 ? page_end - scope : 1;
                }

                $pagination.find('li.prev a').attr("href", kanban_url_col+(page-1 > 0 ? page-1 : 1));
                $pagination.find('li.next a').attr("href", kanban_url_col+(page < page_end ? page+1 : page_end));
                for(var i=0; i < scope; i++) {
                    $pagination.find('li:not(.prev):not(.next):eq('+i+') a').attr("href", kanban_url_col+(page_start+i)).html(page_start+i);
                }
                $pagination.find('li.active').removeClass('active');
                $pagination.find('li:has(a[href="'+kanban_url_col+page+'"])').addClass('active');

            });

        });
    };

    /* ----------------------------------------------------
       Async Ready and Template loading
       ---------------------------------------------------- */ 
    var templates_def = $.Deferred().resolve();
    website.add_template_file = function(template) {
        var def = $.Deferred();
        templates_def = templates_def.then(function() {
            openerp.qweb.add_template(template, function(err) {
                if (err) {
                    def.reject(err);
                } else {
                    def.resolve();
                }
            });
            return def;
        });
        return def;
    };

    website.dom_ready = $.Deferred();
    $(document).ready(function () {
        website.dom_ready.resolve();
        // fix for ie
        if($.fn.placeholder) $('input, textarea').placeholder();
    });

    /**
     * Execute a function if the dom contains at least one element matched
     * through the given jQuery selector. Will first wait for the dom to be ready.
     *
     * @param {String} selector A jQuery selector used to match the element(s)
     * @param {Function} fn Callback to execute if at least one element has been matched
     */
    website.if_dom_contains = function(selector, fn) {
        website.dom_ready.then(function () {
            var elems = $(selector);
            if (elems.length) {
                fn(elems);
            }
        });
    };

    var all_ready = null;
    /**
     * Returns a deferred resolved when the templates are loaded
     * and the Widgets can be instanciated.
     */
    website.ready = function() {
        if (!all_ready) {
            all_ready = website.dom_ready.then(function () {
                return templates_def;
            }).then(function () {
                // display button if they are at least one editable zone in the page (check the branding)
                if ($('[data-oe-model]').size()) {
                    $("#oe_editzone").show();
                }

                if ($('html').data('website-id')) {
                    website.id = $('html').data('website-id');
                    website.session = new openerp.Session();
                    return openerp.jsonRpc('/website/translations', 'call', {'lang': website.get_context().lang})
                    .then(function(trans) {
                        openerp._t.database.set_bundle(trans);});
                }
            }).then(function () {
                var templates = openerp.qweb.templates;
                var keys = _.keys(templates);
                for (var i = 0; i < keys.length; i++){
                    treat_node(templates[keys[i]]);
                }
            }).promise();
        }
        return all_ready;
    };

    function treat_node(node){
        if(node.nodeType === 3) {
            if(node.nodeValue.match(/\S/)){
                var text_value = $.trim(node.nodeValue);
                var spaces = node.nodeValue.split(text_value);
                node.nodeValue = spaces[0] + openerp._t(text_value) + spaces[1];
            }
        }
        else if(node.nodeType === 1 && node.hasChildNodes()) {
            _.each(node.childNodes, function(subnode) {treat_node(subnode);});
        }
    };

    website.inject_tour = function() {
        // if a tour is active inject tour js
    };

    website.dom_ready.then(function () {
        /* ----- PUBLISHING STUFF ---- */
        $(document).on('click', '.js_publish_management .js_publish_btn', function () {
            var $data = $(this).parents(".js_publish_management:first");
            var self=this;
            openerp.jsonRpc($data.data('controller') || '/website/publish', 'call', {'id': +$data.data('id'), 'object': $data.data('object')})
                .then(function (result) {
                    $data.toggleClass("css_unpublished css_published");
                    $data.parents("[data-publish]").attr("data-publish", +result ? 'on' : 'off');
                }).fail(function (err, data) {
                    website.error(data, '/web#return_label=Website&model='+$data.data('object')+'&id='+$data.data('id'));
                });
        });

        if (!$('.js_change_lang').length) {
            // in case template is not up to date...
            var links = $('ul.js_language_selector li a:not([data-oe-id])');
            var m = $(_.min(links, function(l) { return $(l).attr('href').length; })).attr('href');
            links.each(function() {
                var t = $(this).attr('href');
                var l = (t === m) ? "default" : t.split('/')[1];
                $(this).data('lang', l).addClass('js_change_lang');
            });
        }

        $(document).on('click', '.js_change_lang', function(e) {
            e.preventDefault();

            var self = $(this);
            // retrieve the hash before the redirect
            var redirect = {
                lang: self.data('lang'),
                url: self.attr('href'),
                hash: location.hash
            };
            location.href = _.str.sprintf("/website/lang/%(lang)s?r=%(url)s%(hash)s", redirect);
        });

        /* ----- KANBAN WEBSITE ---- */
        $('.js_kanban').each(function () {
            website.init_kanban(this);
        });

        setTimeout(function () {
            if (window.location.hash.indexOf("scrollTop=") > -1) {
                window.document.body.scrollTop = +location.hash.match(/scrollTop=([0-9]+)/)[1];
            }
        },0);

        /* ----- WEBSITE TOP BAR ---- */
        var $collapse = $('#oe_applications ul.dropdown-menu').clone()
                .attr("id", "oe_applications_collapse")
                .attr("class", "nav navbar-nav navbar-left navbar-collapse collapse");
        $('#oe_applications').before($collapse);
        $collapse.wrap('<div class="visible-xs"/>');
        $('[data-target="#oe_applications"]').attr("data-target", "#oe_applications_collapse");
    });

    openerp.Tour.autoRunning = false;
    website.ready().then(function () {
        setTimeout(openerp.Tour.running,0);
    });

    return website;
})();
