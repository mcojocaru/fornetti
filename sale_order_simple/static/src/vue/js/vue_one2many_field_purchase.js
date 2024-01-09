
odoo.define('sale_order_simple.purchase_widgets', function (require) {

    "use strict";

    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var field_registry = require('web.field_registry');
    var field_utils = require('web.field_utils');

    var QWeb = core.qweb;
    var _t = core._t;

    var FieldChar = require('web.basic_fields').FieldChar;

    var _vue_app_proxy = null;
    function register_vue_app_proxy(proxy) {
       _vue_app_proxy = proxy;
    };


    const init_vue_app = async function init_vue_app() {
		const vue_app = await Vue.createApp({
			template: `
				   <table className="table table-striped table-bordered table-sm">
						<thead className="thead-light">
							<th>Produs</th>
							<th>Cantitate</th>
							<th>Pret Unitar</th>
							<th>UM</th>
							<th>Comanda</th>
							<th>Total</th>
						</thead>
						<tbody>
							<custom-row v-for="line in lines" :key="line.order_line_id" :line="line"
										@qty-changed="quantityChanged"/>
						</tbody>
					</table>
			`,
			data() {
				return {
					lines: [],
					odoo_field: null,
				};
			},
			mounted() {
				this.lines = JSON.parse(this.ext_lines._getValue());
				this.odoo_field = this.ext_lines;
			},
			created(){
				register_vue_app_proxy(this);
			},
			methods: {
				quantityChanged(){
					console.log(this.lines);
					const raw_data = _.map(Object.assign({}, this.lines), (l) => Object.assign({}, l));
					this.odoo_field._setValue(JSON.stringify(raw_data));
				},
				updateTable(lines){
					this.lines = lines;
				}
			}
		});

		vue_app.component('custom-row', {
			props: ["line"],
			template: `
				<tr v-if="!line.is_section"
					:key="line.order_line_id">
					<td>{{line.product_name}}</td>
					<td>
					   <input v-if="line.disabled" type="number" disabled v-model.number="qty"/>
					   <input v-else type="number" v-model.number="qty"/>
					</td>
					<td>{{line.price_unit}}</td>
					<td>{{line.product_uom_name}}</td>
					<td :style="{border: line.uom_po_qty_flag ? '2px solid red': '1px solid #dee2e6'}">
						{{line.uom_po_qty_name}}
					</td>
					<td>{{line.price_total}}</td>
				</tr>
				<tr v-else className="table-primary" :key="line.order_line_id + '_1'">
					<td>{{line.product_name}}</td>
					<td>{{line.current_qty}}</td>
					<td></td>
					<td></td>
					<td></td>
					<td>{{line.price_total}}</td>
				</tr>
			`,
			data() {
				return {
					qty: this.line.current_qty,
					time_out: null
				}
			},
			watch: {
				qty: function (newQty, oldQty) {
				  if (newQty !== "") {
					  this.line.current_qty = parseInt(newQty);
				  } else {
					  this.line.current_qty = 0;
				  }
				  //this.emit_lazy_qty_changed();
				  this.$emit("qty-changed")
				}
			},
			methods: {
				emit_lazy_qty_changed(){
                    if (this.time_out) {
                        clearTimeout(this.time_out);
                    }
                    this.time_out = setTimeout(() => this.$emit("qty-changed"), 1000);
				}
			}
		});
		return vue_app;
	};
	const vue_app_= init_vue_app();

	var VueFieldChar1 = AbstractField.extend({
		template: "VueTmpl",
		init: function (parent, name, record, options) {
			 this._super.apply(this, arguments);
			 this.vue_app = vue_app_;
			 _vue_app_proxy = null;
		},

		reset: function (record, event) {
			var def = this._super.apply(this, arguments);
			console.log("RESET:", record);
			 if (_vue_app_proxy) {
				_vue_app_proxy.updateTable(JSON.parse(record.data.lines_json2));
			 }
			return def;
		},

		_render: function () {
			this.$el.find('.o_field_value').text(this.value);
			var lines_json1 = this.getParent().getChildren().find((child) => child.name === 'lines_json1');
			if (! _vue_app_proxy) {
				lines_json1.do_hide();
				var self = this;
				return this.vue_app.then(function(res) {
					res.config.globalProperties.ext_lines = lines_json1;
					res.mount(self.$el.find('#vue_root')[0])
				});
			}
		},

	});

	var fieldRegistry = require('web.field_registry');

	fieldRegistry.add('vue_one2many_field_purchase', VueFieldChar1);


    return {
        VueFieldChar1: VueFieldChar1
    };

});
