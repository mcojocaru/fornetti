
odoo.define('sale_order_simple.purchase_widgets', function (require) {

    "use strict";

    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var field_registry = require('web.field_registry');
    var field_utils = require('web.field_utils');

    var QWeb = core.qweb;
    var _t = core._t;

    var FieldChar = require('web.basic_fields').FieldChar;


        class TableRow extends React.Component {

          constructor(props) {
            super(props);
            this.state = {qty: this.props.qty};
          }

//          static getDerivedStateFromProps(props, state) {
//             if (props.qty === 0) {
//                 state.qty = props.qty;
//             }
//             return state;
//          }

          valueChangedHandler = (event) => {
              if (! isNaN(event.target.value)) {
                  this.setState({qty : event.target.value});
                  this.props.changed(event, this.props.index);
              }
          }

          render() {
                const style = {
                     border: this.props.line.uom_po_qty_flag ? '2px solid red': '1px solid #dee2e6',
                };
                return <tr>
                        <td>{this.props.line.product_name}</td>
                        <td><input type="text" disabled={this.props.line.disabled == true} value={this.props.line.disabled ? 0 : this.state.qty} onChange={this.valueChangedHandler.bind(this)}/></td>
                        <td>{this.props.line.price_unit}</td>
                        <td>{this.props.line.product_uom_name}</td>
                        <td style={style}>{this.props.line.uom_po_qty_name}</td>
                        <td>{this.props.line.price_total}</td>
                     </tr>
          }
        }

        class Table extends React.Component {
          constructor(props) {
            super(props);
            this.odoo_field = props.odoo_field;
            this.odoo_field_json_lines1 = props.odoo_field_json_lines1;
            this.state = {value:JSON.parse(this.odoo_field.value)};
          }

          valueChangedHandler = (event, index) => {
              const qty = event.target.value;
              const value = this.state.value;
              if (qty !== "") {
                  value[index].current_qty = parseFloat(qty);

                  //this will call onchange in the backend also
                  this.odoo_field_json_lines1._setValue(JSON.stringify(value));
//                  .then(() => {
//                      this.odoo_field_json_lines1.value = JSON.stringify(this.state.value);
//                      this.odoo_field_json_lines1._renderEdit();
//                  });
              }
          }

          update_table(json_val) {
              this.setState({value:JSON.parse(json_val)});
          }

          render() {
              const lines = this.state.value.map((line, index) => {
                  if (!line.is_section) {
                      return <TableRow key={line.id} qty={line.current_qty} line={line} index={index} changed={this.valueChangedHandler.bind(this)}/>;
                  } else {
                      return (
                        <tr className="table-primary" key={line.id}>
                            <td>{line.product_name}</td>
                            <td>{line.current_qty}</td>
                            <td></td>
                            <td></td>
                            <td></td>
                            <td>{line.price_total}</td>
                        </tr>
                      );
                  }
                });

            return (
              <div>
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
                     {lines}
                  </tbody>
                </table>
              </div>
            );
          }
        }

        var ReactFieldChar1 = AbstractField.extend({
            template: "ReactTmpl",
            init: function (parent, name, record, options) {
                 this._super.apply(this, arguments);
            },

            reset: function (record, event) {
                var def = this._super.apply(this, arguments);
                console.log("RESET:", record);
                if (this.react_component) {
                    this.react_component.update_table(record.data.lines_json2);
                }
                return def;
            },

            _render: function () {
                this.$el.find('.o_field_value').text(this.value);
                var lines_json1 = this.getParent().getChildren().find((child) => child.name === 'lines_json1');
                this.react_component = ReactDOM.render(<Table odoo_field={this}
                                                              odoo_field_json_lines1={lines_json1}/>,
                                                       this.$el.find('#react_root')[0]);
            },

        });

        var fieldRegistry = require('web.field_registry');

        fieldRegistry.add('react_one2many_field_purchase', ReactFieldChar1);


    return {
        ReactFieldChar1: ReactFieldChar1
    };

});
