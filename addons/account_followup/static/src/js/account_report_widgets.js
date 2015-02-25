openerp.account_followup = openerp.account_followup || {}

openerp.account_followup.FollowupReportWidgets = openerp.account.ReportWidgets.extend({
    events: _.defaults({
        'click .changeTrust': 'changeTrust',
        'click .followup-action': 'displayManualAction',
    }, openerp.account.ReportWidgets.prototype.events),
    start: function() {
        openerp.qweb.add_template("/account_followup/static/src/xml/account_followup_report.xml");
        return this._super();
    },
    onKeyPress: function(e) {
        e.stopPropagation();
        e.preventDefault();
        var report_name = $("div.page").attr("class").split(/\s+/)[2];
        if ((e.which === 13 || e.which === 10) && (e.ctrlKey || e.metaKey) && report_name == 'followup_report') {
            $('a.btn-primary.followup-email').trigger('click');
            $('a.btn-primary.followup-letter').trigger('click');
            var action_partner_list = [];
            $('a.btn-primary.followup-action').each(function() {
                action_partner_list.push($(this).attr('partner'))
            });
            window.open('?partner_done=all&action_partner_list=' + action_partner_list, '_self');
        }
    },
    changeTrust: function(e) {
        e.stopPropagation();
        e.preventDefault();
        var partner_id = $(e.target).parents('span.dropdown').attr("partner");
        var newTrust = $(e.target).attr("new-trust");
        var color = 'grey';
        switch(newTrust) {
            case 'good':
                color = 'green';
                break;
            case 'bad':
                color = 'red'
                break;
        }
        var model = new openerp.Model('res.partner');
        model.call('write', [[parseInt(partner_id)], {'trust': newTrust}]).then(function (result) {
            $(e.target).parents('span.dropdown').find('i.fa').attr('style', 'color: ' + color + ';')
        });
    },
    displayManualAction: function(e) {
        e.stopPropagation();
        e.preventDefault();
        var line_id = $(e.target).attr("level");
        var followupObj = new openerp.Model('account_followup.followup.line');
        followupObj.query(['manual_action_note', 'manual_action_responsible_id'])
        .filter([['id', '=', line_id]]).first().then(function (result) {
            $("#manualActionModal .modal-body").html(openerp.qweb.render("manualAction", {data: result}));
            $('#manualActionModal').modal('show');
            var $skipButton = $(e.target).siblings('a.followup-skip');
            $skipButton.attr('class', 'btn btn-primary followup-skip');
            $skipButton.text('Done');
        });
    }
});
