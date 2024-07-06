odoo.define("dynamic_access_rights.crawler", function(require) {
    "use strict";
    const ajax = require("web.ajax");
    const FormRenderer = require('web.FormRenderer')
    var core = require('web.core');
    var web_dom = require('web.dom');

    var _t = core._t;
    let dynamics = null

    function getActiveModel(){
        let urlString = window.location.href.split('#')[1]
        const params = new URLSearchParams(urlString);
        return params.get('model')
    }

    function update_buttons(target_buttons, dom){
        for (const [name, restriction] of Object.entries(target_buttons)) {
            let klas = `dynamics-${restriction}`
            if(name){
                let buttons1 = dom.querySelector(`button[name="${name}"]`)
                let buttons2 = dom.querySelector(`.${CSS.escape(name)}`)
                if(buttons1){
                    buttons1.classList.add(klas)
                }
                if(buttons2){
                    buttons2.classList.add(klas)
                }
            }
        }
        return dom
    }
    function update_pages(target_pages, dom){
        for (const [name, restriction] of Object.entries(target_pages)) {
            let klas = `dynamics-${restriction}`
            let anchors = dom.querySelectorAll(`a[role='tab']`)
            anchors.forEach(function (anchor) {
                if (anchor.innerText.toLowerCase() === name.toLowerCase()) {
                    let page_id = anchor.getAttribute('href').slice(1)
                    anchor.classList.add(klas)
                    let tab_content = dom.querySelector(`#${page_id}`)
                    tab_content.classList.add(klas)
                }
            })
        }
        return dom
    }

    function refresh_rights(dom, active_model){
        if(dynamics && active_model) {
            let data = dynamics[active_model]
            if(data && data['buttons']){
                dom = update_buttons(data['buttons'], dom)
            }
            if(data && data['pages']){
                dom = update_pages(data['pages'],dom)
            }
        }
        return dom
    }

    FormRenderer.include({
        refinedButton: function(btn){
            let name = btn.name
            let model = getActiveModel()
            if(name && model){
                let data = dynamics[model]
                let buttons = data && data['buttons']
                if(buttons){
                    let restriction = buttons[name]
                    if(restriction){
                        let klas = `dynamics-${restriction}`
                        btn.classList.add(klas)
                    }
                }
            }
            return btn
        },
        _renderTagNotebook: function (node) {
            let $notebook = this._super.apply(this, arguments);
            let model = getActiveModel()
            $notebook[0] = refresh_rights($notebook[0], model)
            return $notebook
        },

        _renderHeaderButton: function (node) {
            let button = this._super.apply(this, arguments);
            var self = this
            self.refinedButton(button[0])
            return button
        },

        _renderButtonBox: function (node) {
            var self = this;
            var $result = $('<' + node.tag + '>', {class: 'o_not_full'});

            // Hide or disable button if a rule exists

            // The rendering of buttons may be async (see renderFieldWidget), so we
            // must wait for the buttons to be ready (and their modifiers to be
            // applied) before manipulating them, as we check if they are visible or
            // not. To do so, we extract from this.defs the promises corresponding
            // to the buttonbox buttons, and wait for them to be resolved.
            var nextDefIndex = this.defs.length;
            var buttons = _.map(node.children, function (child) {
                if (child.tag === 'button') {
                    return self._renderStatButton(child);
                } else {
                    return self._renderNode(child);
                }
            });

            // At this point, each button is an empty div that will be replaced by
            // the real $el of the button when it is ready (with replaceWith).
            // However, this only works if the empty div is appended somewhere, so
            // we here append them into a wrapper, and unwrap them once they have
            // been replaced.
            var $tempWrapper = $('<div>');
            _.each(buttons, function ($button) {
                $button.appendTo($tempWrapper);
            });
            var defs = this.defs.slice(nextDefIndex);
            Promise.all(defs).then(function () {
                buttons = $tempWrapper.children();
                var buttons_partition = _.partition(buttons, function (button) {
                    return $(button).is('.o_invisible_modifier');
                });
                var invisible_buttons = buttons_partition[0];
                var visible_buttons = buttons_partition[1];

                // Get the unfolded buttons according to window size
                var nb_buttons = self._renderButtonBoxNbButtons();
                var unfolded_buttons = visible_buttons.slice(0, nb_buttons).concat(invisible_buttons);

                // Get the folded buttons
                var folded_buttons = visible_buttons.slice(nb_buttons);
                if (folded_buttons.length === 1) {
                    unfolded_buttons = buttons;
                    folded_buttons = [];
                }

                // Toggle class to tell if the button box is full (CSS requirement)
                var full = (visible_buttons.length > nb_buttons);
                $result.toggleClass('o_full', full).toggleClass('o_not_full', !full);

                // Add the unfolded buttons
                _.each(unfolded_buttons, function (button) {
                    button = self.refinedButton(button) // Check if button needs to be hidden/disabled
                    $(button).appendTo($result);
                });

                // Add the dropdown with folded buttons if any
                if (folded_buttons.length) {
                    $result.append(web_dom.renderButton({
                        attrs: {
                            'class': 'oe_stat_button o_button_more dropdown-toggle',
                            'data-toggle': 'dropdown',
                        },
                        text: _t("More"),
                    }));

                    var $dropdown = $("<div>", {class: "dropdown-menu o_dropdown_more", role: "menu"});
                    _.each(folded_buttons, function (button) {
                        button = self.refinedButton(button) // Check if button needs to be hidden/disabled
                        $(button).addClass('dropdown-item').appendTo($dropdown);
                    });
                    $dropdown.appendTo($result);
                }
            });
            this._handleAttributes($result, node);
            this._registerModifiers(node, this.state, $result);
            return $result;
        }
    })

    const set_dynamics = () => {
        return new Promise((resolve, reject) => {
            resolve(
                ajax.jsonRpc("/fetch-dynamic-objects", "call", {},)
                    .then(function (data) {
                        dynamics = data
                    }).catch(function (error) {
                    if (error) {
                    }
                })
            )
            reject("Unable to fetch access rights info from the server")
        })
    }

    QWeb2.Engine.prototype.render = function (template, dict) {

        let model = dict && dict.widget && dict.widget.model
        if(model && typeof (model) != "string"){
            model = model.loadParams.modelName
        }
        set_dynamics()
        dict = dict || {};
        QWeb2.tools.extend(dict, this.default_dict);
        /*if (this.debug && window['console'] !== undefined) {
            console.time("QWeb render template " + template);
        }*/
        var res = this._render(template, dict);
        /*if (this.debug && window['console'] !== undefined) {
            console.timeEnd("QWeb render template " + template);
        }*/
        let el = document.createElement("div")
        el.innerHTML = res
        if(model) {
            res = refresh_rights(el, model).innerHTML
        }
        return res
    }
})
