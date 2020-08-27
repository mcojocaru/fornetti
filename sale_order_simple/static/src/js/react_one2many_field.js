var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass; }

odoo.define('sale_order_simple.widgets', function (require) {

    "use strict";

    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var field_registry = require('web.field_registry');
    var field_utils = require('web.field_utils');

    var QWeb = core.qweb;
    var _t = core._t;

    var FieldChar = require('web.basic_fields').FieldChar;

    var TableRow = function (_React$Component) {
        _inherits(TableRow, _React$Component);

        function TableRow(props) {
            _classCallCheck(this, TableRow);

            var _this = _possibleConstructorReturn(this, (TableRow.__proto__ || Object.getPrototypeOf(TableRow)).call(this, props));

            _this.valueChangedHandler = function (event) {
                if (!isNaN(event.target.value)) {
                    if (parseFloat(event.target.value || '0') <= parseFloat(_this.props.line.free_qty)) {
                        _this.setState({ qty: event.target.value });
                        _this.props.changed(event, _this.props.index);
                    }
                }
            };

            _this.state = { qty: _this.props.line.current_qty };
            return _this;
        }

        _createClass(TableRow, [{
            key: 'render',
            value: function render() {
                return React.createElement(
                    'tr',
                    null,
                    React.createElement(
                        'td',
                        null,
                        this.props.line.product_name
                    ),
                    React.createElement(
                        'td',
                        null,
                        this.props.line.free_qty
                    ),
                    React.createElement(
                        'td',
                        null,
                        React.createElement('input', { type: 'text', value: this.state.qty, onChange: this.valueChangedHandler.bind(this) })
                    ),
                    React.createElement(
                        'td',
                        null,
                        this.props.line.sold_qty
                    ),
                    React.createElement(
                        'td',
                        null,
                        this.props.line.is_section ? this.props.line.sold_qty_adjusted : ''
                    ),
                    React.createElement(
                        'td',
                        null,
                        this.props.line.price_unit
                    ),
                    React.createElement(
                        'td',
                        null,
                        this.props.line.product_uom_name
                    ),
                    React.createElement(
                        'td',
                        null,
                        this.props.line.is_section ? this.props.line.price_total : ''
                    )
                );
            }
        }]);

        return TableRow;
    }(React.Component);

    var Table = function (_React$Component2) {
        _inherits(Table, _React$Component2);

        function Table(props) {
            _classCallCheck(this, Table);

            var _this2 = _possibleConstructorReturn(this, (Table.__proto__ || Object.getPrototypeOf(Table)).call(this, props));

            _this2.valueChangedHandler = function (event, index) {
                var qty = event.target.value;
                var value = _this2.state.value;
                if (qty !== "") {
                    value[index].current_qty = parseFloat(qty);

                    //this will call onchange in the backend also
                    _this2.odoo_field_json_lines1._setValue(JSON.stringify(value));
                    //                  .then(() => {
                    //                      this.odoo_field_json_lines1.value = JSON.stringify(this.state.value);
                    //                      this.odoo_field_json_lines1._renderEdit();
                    //                  });
                }
            };

            _this2.odoo_field = props.odoo_field;
            _this2.odoo_field_json_lines1 = props.odoo_field_json_lines1;
            _this2.state = { value: JSON.parse(_this2.odoo_field.value) };
            return _this2;
        }

        _createClass(Table, [{
            key: 'update_table',
            value: function update_table(json_val) {
                this.setState({ value: JSON.parse(json_val) });
            }
        }, {
            key: 'render',
            value: function render() {
                var _this3 = this;

                var lines = this.state.value.map(function (line, index) {
                    if (!line.is_section) {
                        return React.createElement(TableRow, { key: line.id, line: line, index: index, changed: _this3.valueChangedHandler.bind(_this3) });
                    } else {
                        return React.createElement(
                            'tr',
                            { className: 'table-primary', key: line.id },
                            React.createElement(
                                'td',
                                null,
                                line.product_name
                            ),
                            React.createElement('td', null),
                            React.createElement(
                                'td',
                                null,
                                line.current_qty
                            ),
                            React.createElement(
                                'td',
                                null,
                                line.sold_qty
                            ),
                            React.createElement(
                                'td',
                                null,
                                line.sold_qty_adjusted
                            ),
                            React.createElement('td', null),
                            React.createElement('td', null),
                            React.createElement(
                                'td',
                                null,
                                line.price_total
                            )
                        );
                    }
                });

                return React.createElement(
                    'div',
                    null,
                    React.createElement(
                        'table',
                        { className: 'table table-striped table-bordered table-sm' },
                        React.createElement(
                            'thead',
                            { className: 'thead-light' },
                            React.createElement(
                                'th',
                                null,
                                'Produs'
                            ),
                            React.createElement(
                                'th',
                                null,
                                'Cantitate Initiala'
                            ),
                            React.createElement(
                                'th',
                                null,
                                'Cantitate Ramasa'
                            ),
                            React.createElement(
                                'th',
                                null,
                                'Cantitate Vanduta (fara pierderi)'
                            ),
                            React.createElement(
                                'th',
                                null,
                                'Cantitate Vanduta (cu pierderi)'
                            ),
                            React.createElement(
                                'th',
                                null,
                                'Pret Unitar'
                            ),
                            React.createElement(
                                'th',
                                null,
                                'UM'
                            ),
                            React.createElement(
                                'th',
                                null,
                                'Total'
                            )
                        ),
                        React.createElement(
                            'tbody',
                            null,
                            lines
                        )
                    )
                );
            }
        }]);

        return Table;
    }(React.Component);

    var ReactFieldChar = AbstractField.extend({
        template: "ReactTmpl",
        init: function init(parent, name, record, options) {
            this._super.apply(this, arguments);
        },

        reset: function reset(record, event) {
            var def = this._super.apply(this, arguments);
            console.log("RESET:", record);
            if (this.react_component) {
                this.react_component.update_table(record.data.lines_json2);
            }
            return def;
        },

        _render: function _render() {
            this.$el.find('.o_field_value').text(this.value);
            var lines_json1 = this.getParent().getChildren().find(function (child) {
                return child.name === 'lines_json1';
            });
            this.react_component = ReactDOM.render(React.createElement(Table, { odoo_field: this,
                odoo_field_json_lines1: lines_json1 }), this.$el.find('#react_root')[0]);
        }

    });

    var fieldRegistry = require('web.field_registry');

    fieldRegistry.add('react_one2many_field', ReactFieldChar);

    return {
        ReactFieldChar: ReactFieldChar
    };
});