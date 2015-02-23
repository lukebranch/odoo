openerp.account_followup = openerp.account_followup || {}

openerp.account_followup.FollowupReportWidgets = openerp.account.ReportWidgets.extend({
    events: _.defaults({
        'click .changeTrust': 'changeTrust',
        'click .followup-action': 'displayManualAction',
    }, openerp.account.ReportWidgets.prototype.events),
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
        var contextObj = new openerp.Model('account_followup.followup.line');
        contextObj.query(['manual_action_note', 'manual_action_responsible_id'])
        .filter([['id', '=', line_id]]).first().then(function (context) {
            
        });
    }
});
