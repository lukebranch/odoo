# -*- coding: utf-8 -*-

from openerp.tests import common


class TestMarketingCampaign(common.TransactionCase):

    def test_00_marketing_campaign_tests(self):

        # In order to test process of compaign, I start compaign.
        partnerchannel = self.env.ref(
            'marketing_campaign.marketing_campaign_openerppartnerchannel')
        partnerchannel.signal_workflow('state_running_set')

        # I check the campaign on Running mode after started.
        self.assertEqual(partnerchannel.state, 'running')

        # I start this segment after assinged campaign.
        segment0 = self.env.ref(
            'marketing_campaign.marketing_campaign_segment0')
        segment0.signal_workflow('state_running_set')

        # I check the segment on Running mode after started.
        self.assertEqual(segment0.state, 'running')

        # I synchronized segment manually to see all step of activity and
        # process covered on this campaign.
        model = self.env['marketing.campaign.segment']
        assert segment0.date_next_sync, 'Next Synchronization date is not calculated.'
        model.synchroniz(segment0)

        # I cancel Marketing Workitems.
        workitem = self.env['marketing.campaign.workitem']
        workitem_rec1 = workitem.search(
            [('segment_id', '=', segment0.id), ('campaign_id', '=', partnerchannel.id)])
        workitem_rec1.button_cancel()
        record1 = workitem.browse(workitem_rec1.ids[0])
        assert record1.state == 'cancelled' or record1.state == 'done', 'Marketing Workitem shoud be in cancel state.'

        # I set Marketing Workitems in draft state.
        workitem_rec1.button_draft()
        assert record1.state == 'todo' or record1.state == 'done', 'Marketing Workitem shoud be in draft state.'

        # I process follow-up of first activity.
        workitem_rec2 = workitem.search([('segment_id', '=', segment0.id),
                                         ('campaign_id', '=', partnerchannel.id), ('activity_id', '=', segment0.id)])
        assert workitem_rec2.ids, 'Follow-up item is not created for first activity.'
        work_item_id = workitem.browse(workitem_rec2.ids[0])
        assert work_item_id.res_name, 'Resource Name is not defined.'
        workitem_rec2.process()
        record2 = workitem.browse(workitem_rec2.ids)
        assert record2.state == "done", "Follow-up item should be closed after process."

        # I check follow-up detail of second activity after process of first
        # activity.
        activity1 = self.env.ref(
            'marketing_campaign.marketing_campaign_activity_1')
        workitem_rec3 = workitem.search([('segment_id', '=', segment0.id), ('campaign_id', '=', partnerchannel.id), (
            'activity_id', '=', activity1.id)])

        assert workitem_rec3.ids, 'Follow - up item is not created for second activity.'

        # Now I increase credit limit of customer
        self.env.ref('base.res_partner_2').write({'credit_limit': 41000})

        # I process follow-up of second activity after set draft.
        workitem_rec3.button_draft()
        workitem_rec3.process()
        record3 = workitem.browse(workitem_rec3.ids)
        assert record3.state == "done", "Follow-up item should be closed after process."

        # I check follow-up detail of third activity after process of second
        # activity.
        activity2 = self.env.ref(
            'marketing_campaign.marketing_campaign_activity_2')
        workitem_rec4 = workitem.search([('segment_id', '=', segment0.id), ('campaign_id', '=', partnerchannel.id), (
            'activity_id', '=', activity2.id)])
        assert workitem_rec4.ids, 'Follow-up item is not created for third activity.'

        # Now I increase credit limit of customer
        self.env.ref('base.res_partner_2').write({'credit_limit': 151000})

        # I process follow-up of third activity after set draft.
        workitem_rec4.button_draft()
        workitem_rec4.process()
        record4 = workitem.browse(workitem_rec4.ids[0])
        assert record4.state == "done", "Follow-up item should be closed after process."

        # I print workitem report.
        workitem_rec4.preview()

        # I cancel segmentation because of some activity.
        segment0.signal_workflow('state_cancel_set')

        # I check the segmentation is canceled.
        self.assertEqual(segment0.state, 'cancelled')

        # I reopen the segmentation.
        segment0.signal_workflow('state_draft_set')
        segment0.signal_workflow('state_running_set')

        # I check the segment on Running mode after started.
        self.assertEqual(segment0.state, 'running')

        # I close segmentation After completion of all activity.
        segment0.signal_workflow('state_done_set')

        # I check the segmentation is done.
        self.assertEqual(segment0.state, 'done')

        # I close this campaign.
        partnerchannel.signal_workflow('state_done_set')

        # I check the campaing is done.
        self.assertEqual(partnerchannel.state, 'done')
