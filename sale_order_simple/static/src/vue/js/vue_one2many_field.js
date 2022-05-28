odoo.define('sale_order_simple.widgets', function(require) {

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

    function init_vue_app() {
		const vue_app = Vue.createApp({
			template: `
				<table className="table table-striped table-bordered table-sm" ref="">
				  <thead className="thead-light">
					<th>Produs</th>
					  <th>Cantitate Initiala</th>
					  <th>Cantitate Ramasa</th>
					  <th>Cantitate Vanduta (fara pierderi)</th>
					  <th>Cantitate Vanduta (cu pierderi)</th>
					  <th>Pret Unitar</th>
					  <th>UM</th>
					  <th>Total</th>
				  </thead>
					<tbody>
					 <custom-row v-for="line in lines" :key="line.id" :line="line"
								 @qty-changed="quantityChanged"
					 />
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
				<tr v-if="!line.is_section">
					<td>{{line.product_name}}</td>
					<td>{{line.qty_available.toFixed(1)}}</td>
					<td :style="{border: err_cell ? '2px solid red': '1px solid #dee2e6'}">
					   <input type="number" v-model.number="qty"/>
					</td>
					<td>{{ line.sold_qty && line.sold_qty.toFixed(1) }}</td>
					<td>{{ line.is_section? line.sold_qty_adjusted.toFixed(1): '' }}</td>
					<td>{{ line.price_unit }}</td>
					<td>{{ line.product_uom_name }}</td>
					<td>{{ line.is_section? line.price_total && line.price_total.toFixed(1): '' }}</td>
				</tr>
				<tr v-else className="table-primary">
					<td>{{line.product_name}}</td>
					<td></td>
					<td>{{ line.current_qty.toFixed(1) }}</td>
					<td>{{ line.sold_qty && line.sold_qty.toFixed(1) }}</td>
					<td>{{ line.sold_qty_adjusted && line.sold_qty_adjusted.toFixed(1) }}</td>
					<td></td>
					<td></td>
					<td>{{ line.price_total && line.price_total.toFixed(1) }}</td>
				</tr>
			`,
			data() {
				return {
					qty: this.line.qty,
					time_out: null
				}
			},
			watch: {
				qty: function (newQty, oldQty) {
					if (this.line.product_uom_name === 'kg') {
						if (newQty !== "" && parseFloat(newQty) <= this.line.qty_available) {
							this.line.current_qty = parseFloat(newQty);
							this.qty = parseFloat(newQty);
						} else {
							if (newQty === "") {
								this.line.current_qty = 0;
							} else {
								this.line.current_qty = Math.min(this.line.qty_available, parseFloat(oldQty));
							}
						}
					} else {
						if (newQty !== "" && parseInt(newQty) <= this.line.qty_available) {
							this.line.current_qty = parseInt(newQty);
							this.qty = parseInt(newQty);
						} else {
							if (newQty === "") {
								this.line.current_qty = 0;
							} else {
								this.line.current_qty = Math.min(this.line.qty_available, parseInt(oldQty));
							}
						}
				  }
				  //this.$emit('qty-changed');
				  this.emit_lazy_qty_changed();
				}
			},
			methods: {
//				emit_lazy_qty_changed: _.debounce(function(){
//					this.$emit("qty-changed");
//				}, 1000)
                emit_lazy_qty_changed(){
                    if (this.time_out) {
                        clearTimeout(this.time_out);
                    }
                    this.time_out = setTimeout(() => this.$emit("qty-changed"), 1000);
				}
			},
			computed: {
				err_cell() {
					return this.qty > this.line.qty_available
				}
			}
		});
		return vue_app;
	};

    var VueFieldChar = AbstractField.extend({
        template: "VueTmpl",
        init: function(parent, name, record, options) {
            this._super.apply(this, arguments);
            this.vue_app = init_vue_app();
            _vue_app_proxy = null;
        },

        reset: function(record, event) {
            var def = this._super.apply(this, arguments);
            console.log("RESET:", record);
            if (_vue_app_proxy) {
                _vue_app_proxy.updateTable(JSON.parse(record.data.lines_json2));
            }
            return def;
        },

        _render: function() {
            this.$el.find('.o_field_value').text(this.value);
            var lines_json1 = this.getParent().getChildren().find((child) => child.name === 'lines_json1');
            if (! _vue_app_proxy) {
            	lines_json1.do_hide();
				this.vue_app.config.globalProperties.ext_lines = lines_json1;
				this.vue_app.mount(this.$el.find('#vue_root')[0])
            }
        },

    });

    var fieldRegistry = require('web.field_registry');

    fieldRegistry.add('vue_one2many_field', VueFieldChar);


    return {
        VueFieldChar: VueFieldChar
    };

});