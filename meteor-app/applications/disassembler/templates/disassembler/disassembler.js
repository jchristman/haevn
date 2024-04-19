if (Meteor.isClient) {
    Template.disassembler.helpers({
        disassemblyLines : function() {
            return Disassembler.find().count() > 0;
        },

        setup : function() {
            var _columns = [
                {
                    name : 'Section',
                    varName : 'sec_name',
                    class : 'sec'
                },
                {
                    name : 'Address',
                    varName : 'addr',
                    class : 'addr',
                    transform : addr_transform
                },
                {
                    name : 'Mnemonic',
                    varName : 'mnemonic',
                    class : 'mnem'
                },
                {
                    name : 'Operands',
                    varName : 'operands',
                    class : 'op',
                    transform : op_transform
                }
            ];
            var _css = {
                table_class : 'disassembler-table',
                row_class : 'disassembler-row',
            }
            return { columns : _columns, css : _css };
        }
    });
    
    Template.no_disassembly.events({
        'click .no_disassembly' : function(event) {
            MeteorOS.getApp('File Dialog').call('openFile', function(file) {
                MeteorOS.Alerts.Info('Starting to disassemble ' + file.name());
                Meteor.call('disassemble', file.file());
            });
        }
    });

    var addr_transform = function(data) {
        return disp(data, 'hex');
    }

    var op_transform = function(data, context) {
        var section = context.sec_name;

        var transformed = '';
        _.each(data, function(operand) {
            switch (operand.type) {
                case "fp":
                    transformed += wrapAndReg({val : operand.fp.val, disp : operand.fp.disp});
                    break;
                case "imm":
                    transformed += wrapAndReg({val : operand.imm.val, disp : operand.imm.disp});
                    break;
                case "inv":
                    console.log("INVALID");
                    console.log(operand);
                    break;
                case "mem":
                    transformed += wrap('dword ptr[','op');
                    
                    if (operand.base != 0) {
                        transformed += wrap(operand.base, 'op'); // Add a register name
                        if (operand.rel.val < 0) transformed += wrap(' - ','op') + wrapAndReg({val : operand.rel.val * -1, disp : operand.rel.disp});
                        if (operand.rel.val > 0) transformed += wrap(' + ','op') + wrapAndReg({val : operand.rel.val, disp : operand.rel.disp});
                    } else {
                        transformed += wrapAndReg({val : operand.rel.val, disp : operand.rel.disp});
                    }
                    
                    if (operand.index != 0) {
                        transformed += wrap(' + ' + operand.index, "op");
                        if (operand.scale.val != 1)
                            transformed += wrap('*','op') + wrapAndReg({val : operand.scale.val, disp : operand.scale.disp});
                    }

                    transformed += wrap(']', 'op');
                    break;
                case "reg":
                    transformed += wrap(operand.reg, 'op');
                    break;
            }

            if (operand.last != true) transformed += ",";
        });

        var html = new Handlebars.SafeString(transformed);
        return html;
    }

    var wrapAndReg = function(data) {
        return wrap(disp(data.val, data.disp), 'op'); // TODO: possibly get rid of this. Will need to see if we need it
    }

    var wrap = function(data, cls) {
        if (typeof cls == 'undefined')
            return '<div>' + data + '</div>';
        return '<div class="'+cls+'">' + data + '</div>';
    }
}
