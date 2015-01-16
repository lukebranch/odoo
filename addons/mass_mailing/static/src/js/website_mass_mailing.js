(function () {
    'use strict';

    var website = openerp.website;

    website.snippet.animationRegistry.subscribe = website.snippet.Animation.extend({
        selector: ".js_subscribe",
        start: function (editable_mode) {
            var self = this;

            // set value and display button
            self.$target.find("input").removeClass("hidden");
            openerp.jsonRpc('/website_mass_mailing/is_subscriber', 'call', {
                list_id: this.$target.data('list-id'),
            }).always(function (data) {
                self.$target.find('input.js_subscribe_email')
                    .val(data.email ? data.email : "")
                    .attr("disabled", data.is_subscriber && data.email.length ? "disabled" : false);
                self.$target.attr("data-subscribe", data.is_subscriber ? 'on' : 'off');
                self.$target.find('a.js_subscribe_btn')
                    .attr("disabled", data.is_subscriber && data.email.length ? "disabled" : false);
                self.$target.removeClass("hidden");
                self.$target.find('.js_subscribe_btn').toggleClass('hidden', !!data.is_subscriber);
                self.$target.find('.js_subscribed_btn').toggleClass('hidden', !data.is_subscriber);
            });

            // not if editable mode to allow designer to edit alert field
            if (!editable_mode) {
                $('.js_subscribe > .alert').addClass("hidden");
                $('.js_subscribe > .input-group-btn.hidden').removeClass("hidden");
                this.$target.find('.js_subscribe_btn').on('click', function (event) {
                    event.preventDefault();
                    self.on_click();
                });
            }
        },
        on_click: function () {
            var self = this;
            var $email = this.$target.find(".js_subscribe_email:visible");

            if ($email.length && !$email.val().match(/.+@.+/)) {
                this.$target.addClass('has-error');
                return false;
            }
            this.$target.removeClass('has-error');

            openerp.jsonRpc('/website_mass_mailing/subscribe', 'call', {
                'list_id': this.$target.data('list-id'),
                'email': $email.length ? $email.val() : false,
            }).then(function (subscribe) {
                self.$target.find(".js_subscribe_email, .input-group-btn").addClass("hidden");
                self.$target.find(".alert").removeClass("hidden");
                self.$target.find('input.js_subscribe_email').attr("disabled", subscribe ? "disabled" : false);
                self.$target.attr("data-subscribe", subscribe ? 'on' : 'off');
            });
        },
    });

    openerp.website.if_dom_contains('div.o_unsubscribe_form', function() {
        $('#unsubscribe_form').on('submit', function(e) {
            e.preventDefault();

            var email = $("input[name='email']").val();
            var mailing_id = parseInt($("input[name='mailing_id']").val());

            var checked_ids = [];
            $("input[type='checkbox']:checked").each(function(i){
              checked_ids[i] = parseInt($(this).val());
            });

            var unchecked_ids = [];
            $("input[type='checkbox']:not(:checked)").each(function(i){
              unchecked_ids[i] = parseInt($(this).val());
            });

            openerp.jsonRpc('/mail/mailing/unsubscribe', 'call', {'opt_in_ids': checked_ids, 'opt_out_ids': unchecked_ids, 'email': email, 'mailing_id': mailing_id})
                .then(function(result) {
                    $('.alert-info').html('Your changes has been saved.').removeClass('alert-info').addClass('alert-success');
                })
                .fail(function() {
                    $('.alert-info').html('You changes has not been saved, try again later.').removeClass('alert-info').addClass('alert-warning');
                }); 
        });
    });

    $('input[name=unsubscription_reason]').change(function(e){
         if (this.id == 'rdo_unsubscribe') {
            $('.spec_reason').show();
            $('.spec_reason').attr('required', '');
         } else {
            $('.spec_reason').hide();
            $('.spec_reason').removeAttr('required');
         }
    });

    $('.cancel_tab').click(function(){
        var i= confirm('Are you sure you want to cancel?');
        if(i == true)
            window.close();
        else
            this.close();

    })
})();
