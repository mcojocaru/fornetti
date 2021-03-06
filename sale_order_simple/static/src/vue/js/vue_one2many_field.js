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
		    <tr v-if="!line.is_section">
				<td>{{line.product_name}}</td>
				<td>{{line.qty_available}}</td>
				<td><input type="number" v-model="qty"/></td>
				<td>{{line.sold_qty}}</td>
				<td>{{line.is_section? line.sold_qty_adjusted: ''}}</td>
				<td>{{line.price_unit}}</td>
				<td>{{line.product_uom_name}}</td>
				<td>{{line.is_section? line.price_total: ''}}</td>
			</tr>
			<tr v-else className="table-primary">
				<td>{{line.product_name}}</td>
				<td></td>
				<td>{{line.current_qty}}</td>
				<td>{{line.sold_qty}}</td>
				<td>{{line.sold_qty_adjusted}}</td>
				<td></td>
				<td></td>
				<td>{{line.price_total}}</td>
			</tr>
		`,
		data() {
		    return {
		        qty: this.line.qty,
		    }
		},
		watch: {
			qty: function (newQty, oldQty) {
			  this.line.current_qty = newQty;
			  this.emit_lazy_qty_changed();
			}
  	    },
  	    methods: {
  	        emit_lazy_qty_changed: _.debounce(function(){
  	            this.$emit("qty-changed");
  	        }, 1000)
  	    }
    });

    var VueFieldChar = AbstractField.extend({
        template: "VueTmpl",
        init: function(parent, name, record, options) {
            this._super.apply(this, arguments);
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
            //			this.vue_component = ReactDOM.render(<Table odoo_field={this}
            //														  odoo_field_json_lines1={lines_json1}/>,
            //												   this.$el.find('#react_root')[0]);
            if (! _vue_app_proxy) {
				vue_app.config.globalProperties.ext_lines = lines_json1;
				vue_app.mount(this.$el.find('#vue_root')[0])
            }
            this.vue_component = vue_app;
        },

    });

    var fieldRegistry = require('web.field_registry');

    fieldRegistry.add('vue_one2many_field', VueFieldChar);


    return {
        VueFieldChar: VueFieldChar
    };

});