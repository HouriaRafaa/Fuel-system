# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import timedelta


class GSPump(models.Model):
    _name = 'gs.pump'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Pump'
    _rec_name = 'station_id'

    pump_line_ids = fields.One2many('gs.pump.line', 'link_id')
    station_id = fields.Many2one('gs.petrol.station', string='Station')
    is_submitted = fields.Boolean()
    is_create_quotations = fields.Boolean()
    is_admin = fields.Boolean(compute="compute_is_admin", store=True)
    run_compute_int = fields.Integer()
    run_compute_bol = fields.Boolean(compute="compute_run")

    sum_petrol_91 = fields.Float(compute="compute_sum_liter")

    sum_petrol_95 = fields.Float(compute="compute_sum_liter")

    sum_petrol_diesel = fields.Float(compute="compute_sum_liter")

    def compute_sum_liter(self):
        for rec in self:
            rec.sum_petrol_91 = rec.sum_petrol_95 = rec.sum_petrol_diesel = 0

            for line in rec.pump_line_ids:
                if line.type_pump_id == self.env.ref("petrol_station.gs_petrol_91"):
                    rec.sum_petrol_91 += line.opening_pump
                elif line.type_pump_id == self.env.ref("petrol_station.gs_petrol_95"):
                    rec.sum_petrol_95 += line.opening_pump
                elif line.type_pump_id == self.env.ref("petrol_station.gs_diesel"):
                    rec.sum_petrol_diesel += line.opening_pump

    def compute_run(self):
        for rec in self:
            rec.run_compute_bol = False
            rec.run_compute_int += 1
            if rec.run_compute_int == 1000:
                rec.run_compute_int = 0
                rec.run_compute_bol = True

    @api.depends("run_compute_int")
    def compute_is_admin(self):
        for rec in self:
            rec.is_admin = False
            if self.env.user.has_group('petrol_station.group_gs_petrol_station_Admin'):
                rec.is_admin = True

    def action_submit_daily_sales(self):
        for rec in self:
            daily_sales = self.env['gs.daily.sales'].search([("station_id", "=", rec.station_id.id), ("state", "=", 'draft')], order='id desc', limit=1)
            if daily_sales:
                for daily in daily_sales:
                    if daily.date == fields.Date.today():
                        daily.action_submit()
                rec.is_submitted = False
                rec.is_create_quotations = True

    def action_create_quotations_daily_sales(self):
        for rec in self:
            daily_sales = self.env['gs.daily.sales'].search([("station_id", "=", rec.station_id.id), ("state", "=", 'submit')], order='id desc', limit=1)
            if daily_sales:
                for daily in daily_sales:
                    if daily.date == fields.Date.today():
                        daily.action_create_quotations()
                rec.is_create_quotations = False

    def action_set_daily_sales(self):
        for rec in self:
            daily_sales = self.env['gs.daily.sales'].search([("station_id", "=", rec.station_id.id), ("state", "=", 'draft')], order='id desc', limit=1)
            if daily_sales:
                for daily in daily_sales:
                    if daily.date == fields.Date.today():
                        for pump in rec.pump_line_ids:
                            if pump.ending_pump:
                                vals = {
                                    'link_id': daily.id,
                                    'date': fields.Date.today(),
                                    'type_pump_id': pump.type_pump_id.id,
                                    'nozzle_petrol_id': pump.nozzle_petrol_id.id,
                                    'opening_pump': pump.opening_pump,
                                    'ending_pump': pump.ending_pump,
                                    'sales': pump.sales,
                                    'user_id': self.env.user.id,
                                }
                                daily.daily_sales_ids = [(0, 0, vals)]
                        rec.is_submitted = True
                    else:
                        vals_daily = {
                            "station_id": rec.station_id.id,
                            "date": fields.Date.today(),
                            "state": 'draft',
                        }
                        new_daily_sales = self.env['gs.daily.sales'].create(vals_daily)
                        for pump in rec.pump_line_ids:
                            if pump.ending_pump:
                                vals = {
                                    'link_id': daily.id,
                                    'date': fields.Date.today(),
                                    'type_pump_id': pump.type_pump_id.id,
                                    'nozzle_petrol_id': pump.nozzle_petrol_id.id,
                                    'opening_pump': pump.opening_pump,
                                    'ending_pump': pump.ending_pump,
                                    'sales': pump.sales,
                                    'user_id': self.env.user.id,
                                }
                                new_daily_sales.daily_sales_ids = [(0, 0, vals)]
                                rec.is_submitted = True
            else:
                vals_daily = {
                    "station_id": rec.station_id.id,
                    "date": fields.Date.today(),
                    "state": 'draft',
                }
                new_daily_sales = self.env['gs.daily.sales'].create(vals_daily)
                for pump in rec.pump_line_ids:
                    if pump.ending_pump:
                        vals = {
                            'link_id': new_daily_sales.id,
                            'date': fields.Date.today(),
                            'type_pump_id': pump.type_pump_id.id,
                            'nozzle_petrol_id': pump.nozzle_petrol_id.id,
                            'opening_pump': pump.opening_pump,
                            'ending_pump': pump.ending_pump,
                            'sales': pump.sales,
                            'user_id': self.env.user.id,
                        }
                        new_daily_sales.daily_sales_ids = [(0, 0, vals)]
                        rec.is_submitted = True

    @api.onchange('station_id')
    def _onchange_action_station_id(self):
        for rec in self:
            if rec.station_id:
                petrol_station = self.env['gs.petrol.station'].search([("id", "=", rec.station_id.id)])
                if petrol_station:
                    for daily in petrol_station.petrol_station_ids:
                        vals = {
                            'date': fields.Date.today(),
                            'pump': daily.pump,
                            'type_pump_id': daily.type_pump_id.id,
                            'nozzle_petrol_id': daily.nozzle_petrol_id.id,
                            'user_id': self.env.user.id,
                        }
                        rec.pump_line_ids = [(0, 0, vals)]

    def action_create_daily_sales(self, vals_daily):
        daily_sales = self.env['gs.daily.sales'].create(vals_daily)
        self.action_set_daily_sales()
        # daily_sales.action_create_quotations()

    def action_set_line(self):
        for rec in self:
            rec.action_set_daily_sales()
            for pump in rec.pump_line_ids:
                if pump.ending_pump:
                    pump.opening_pump += pump.sales
                    pump.ending_pump = 0
                    pump.sales = 0
                    pump.is_done = True



class GSPumpLine(models.Model):
    _name = 'gs.pump.line'

    link_id = fields.Many2one('gs.pump')

    sequence = fields.Integer(string='Sequence', default=10)
    date = fields.Date(string='Date', )
    pump = fields.Char(string='Pump')
    type_pump_id = fields.Many2one('gs.pump.type', string='Pump Type')
    nozzle_petrol_id = fields.Many2one('gs.nozzle.petrol', string='Nozzle Petrol')
    opening_pump = fields.Float(string='Opening',)
    ending_pump = fields.Float(string='Ending',)
    sales = fields.Float(string='Sales',)
    user_id = fields.Many2one('res.users', string='User')
    is_done = fields.Boolean()

    @api.onchange('ending_pump')
    def _onchange_pump(self):
        for rec in self:
            rec.sales = rec.ending_pump - rec.opening_pump