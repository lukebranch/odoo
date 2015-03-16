# -*- coding: utf-8 -*-

from openerp.tests import common


class TestMarketingCampaign(common.TransactionCase):

    # def setUp(self):
    #     super(TestMarketingCampaign, self).setUp()

    def test_00_marketing_campaign_tests(self):
        # In order to test process of compaign, I start compaign.

        ob = self.env.ref(
            'marketing_campaign.marketing_campaign_openerppartnerchannel')
        m = ob.signal_workflow('state_running_set')
        # I check the campaign on Running mode after started.

        temp = self.assertEqual(ob.state, 'running')

        # I start this segment after assinged campaign.
        a = self.env.ref('marketing_campaign.marketing_campaign_segment0')
        b = a.signal_workflow('state_running_set')
        # I check the segment on Running mode after started.

        c = self.assertEqual(a.state, 'running')

        # I synchronized segment manually to see all step of activity and
        # process covered on this campaign.

        d = self.env['marketing.campaign.segment']
        segment_id = a
        assert segment_id.date_next_sync, 'Next Synchronization date is not calculated.'
        d.synchroniz(a)

        # I cancel Marketing Workitems.
        workitem = self.env['marketing.campaign.workitem']
        item = workitem.search(
            [('segment_id', '=', a.id), ('campaign_id', '=', ob.id)])
        item.button_cancel()
        record = workitem.browse(item.ids[0])
        assert record.state == 'cancelled' or record.state == 'done', 'Marketing Workitem shoud be in cancel state.'

        # I set Marketing Workitems in draft state.
        item.button_draft()
        assert record.state == 'todo' or record.state == 'done', 'Marketing Workitem shoud be in draft state.'

        # I process follow-up of first activity.
        act = workitem.search([('segment_id', '=', a.id),
                               ('campaign_id', '=', ob.id), ('activity_id', '=', self.env.ref('marketing_campaign.marketing_campaign_activity_0').id)])
        assert act.ids, 'Follow-up item is not created for first activity.'
        temp = act.ids[0]
        work_item_id = workitem.browse(act.ids[0])
        assert work_item_id.res_name, 'Resource Name is not defined.'
        act.process()
        process_record = workitem.browse(act.ids)
        assert record.state == "done", "Follow-up item should be closed after process."

        # I check follow-up detail of second activity after process of first
        # activity.
        sec_act = workitem.search([('segment_id', '=', a.id), ('campaign_id', '=', ob.id), (
            'activity_id', '=', self.env.ref('marketing_campaign.marketing_campaign_activity_1').id)])

        assert sec_act.ids, 'Follow - up item is not created for second activity.'

        # Now I increase credit limit of customer
        self.env.ref('base.res_partner_2').write({'credit_limit': 41000})

        # I process follow-up of third activity after set draft.
        th_act = workitem.search([('segment_id', '=', a.id),
                                  ('campaign_id', '=', ob.id), ('activity_id', '=', self.env.ref('marketing_campaign.marketing_campaign_activity_2').id)])
        th_act.button_draft()
        th_act.process()
        th_ids = workitem.browse(th_act.ids[0])

        assert th_ids.state == "done", "Follow-up item should be closed after process."
