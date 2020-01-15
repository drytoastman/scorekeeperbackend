import { LitElement, html, css } from 'lit-element';

// These are the elements needed by this element.
import '@polymer/paper-tabs/paper-tabs.js';
import '@polymer/paper-tabs/paper-tab.js';
import '@polymer/paper-listbox/paper-listbox.js';
import '@polymer/paper-dropdown-menu/paper-dropdown-menu.js';
import '@polymer/paper-item/paper-item.js';
import '@polymer/iron-pages/iron-pages.js';

import { DataSource } from '../datasource.js';
import './entrant-table.js';
import './class-table.js';
import './champ-table.js';
import './toptimes-table.js';
import './runorder-table.js';
import './timer-box.js';


class AnnouncerPanel extends LitElement {

    static get properties() {
        return {
          prev:      { type: Object },
          last:      { type: Object },
          next:      { type: Object },
          lastclass: { type: Object },
          runorder:  { type: Object },
          timer:     { type: Number },

          cselected: { type: Number },
          tselected: { type: Number }
        };
    }

    static get styles() {
        return [css`
            :host {
            }

            .outer {
                display: flex; 
                width: 100%;
            }

            .col1 {
                flex-grow: 1;
            }

            timer-box, runorder-table {
                display: block;
                width: 100%;
            }

            .panel {
                display: flex;
                flex-wrap: wrap;
            }

            .panel * {
                margin: 2px;
                flex-grow: 1;
            }

            .panel paper-dropdown-menu {
                flex: 100%;
                text-align: center;
            }

            paper-tabs {
                font-size: 120%;
            }
          `
        ];
    }

    render() {
        return html`
          <!-- Main content -->
            <div class='outer'>
            <div class='col1'>
                <timer-box .time="${this.timer}"></timer-box>
                <runorder-table .order="${this.runorder}"></runorder-table>

                <div id='classtabs'>
                    <paper-tabs selected="1" @selected-changed="${(e) => { this.cselected = e.target.selected}}">
                    <paper-tab>2nd Last</paper-tab>
                    <paper-tab>Last</paper-tab>
                    <paper-tab>Next</paper-tab>
                    <paper-tab>By Class</paper-tab>
                    </paper-tabs>

                    <iron-pages .selected="${this.cselected}">
                        <div>
                            <entrant-table .entrant="${this.prev ? this.prev.entrant : undefined}"></entrant-table>
                            <class-table       .cls="${this.prev ? this.prev.class   : undefined}"></class-table>
                            <champ-table     .champ="${this.prev ? this.prev.champ   : undefined}"></champ-table>
                        </div>
                        <div class='panel'>
                            <entrant-table .entrant="${this.last ? this.last.entrant : undefined}"></entrant-table>
                            <class-table       .cls="${this.last ? this.last.class   : undefined}"></class-table>
                            <champ-table     .champ="${this.last ? this.last.champ   : undefined}"></champ-table>
                        </div>
                        <div class='panel'>
                            <entrant-table .entrant="${this.next ? this.next.entrant : undefined}"></entrant-table>
                            <class-table       .cls="${this.next ? this.next.class   : undefined}"></class-table>
                            <champ-table     .champ="${this.next ? this.next.champ   : undefined}"></champ-table>
                        </div>
                        <div class='panel'>
                            <paper-dropdown-menu no-animations no-label-float>
                            <paper-listbox slot="dropdown-content" class="dropdown-content" selected="0" @selected-changed="${this.classChange}">
                                <paper-item>Off</paper-item>
                                ${panelConfig.classcodes.map(code => html`<paper-item>${code}</paper-item>`)}
                            </paper-listbox>
                            </paper-dropdown-menu>

                            <entrant-table .entrant="${this.lastclass ? this.lastclass.entrant : undefined}"></entrant-table>
                            <class-table       .cls="${this.lastclass ? this.lastclass.class   : undefined}"></class-table>
                            <champ-table     .champ="${this.lastclass ? this.lastclass.champ   : undefined}"></champ-table>
                        </div>
                    </iron-pages>
                </div>
            </div>

            <div class='col2'>
                <div id='tttabs'>
                    <paper-tabs selected="0" @selected-changed="${(e) => this.tselected = e.target.selected}">
                    <paper-tab>Index</paper-tab>
                    <paper-tab>Raw</paper-tab>
                    </paper-tabs>

                    <iron-pages .selected="${this.tselected}">
                        <div class='panel'>
                            <toptimes-table .order="${this.topnet}" type="Index"></toptimes-table>
                        </div>
                        <div class='panel'>
                            <toptimes-table .order="${this.topraw}" type="Raw"></toptimes-table>
                        </div>
                    </iron-pages>
                </div>
            </div>
            </div>
        `;
    }

    constructor() {
        super();
        var me = this;
        this.classData = null;
        this.dataSource = new DataSource(
            panelConfig.wsurl,
            function(d) {
                if ("last" in d) {
                    me.prev = me.last;
                    me.last = d.last;
                }
                if ("next" in d)    me.next    = d.next;
                if ("topnet" in d)  me.topnet  = d.topnet;
                if ("topraw" in d)  me.topraw  = d.topraw;
                if ("timer" in d)   me.timer   = d.timer;
                if ("runorder" in d) me.runorder = d.runorder;
            }
        );

        this.dataSource.request({
            watch: {
                series:  panelConfig.series,
                eventid: panelConfig.eventid,
                timer:   true,
                runorder: true,
                //protimer: true,
                entrant: true,
                class:   true,
                champ:   true,
                next:    true,
                topnet:  true,
                topraw:  true,
            }
        });
    }

    classChange(e) {
        var idx = e.target.selected;
        var code = e.target.children[idx].textContent;

        if (code == 'Off') {
            if (this.classData != null) {
                this.classData.shutdown();
                this.classData = null;
            }
            this.lastclass = null;
            return;
        }

        var me = this;
        if (this.classData == null) {
            this.classData = new DataSource(
                panelConfig.wsurl,
                (d) => { if ("last" in d) me.lastclass = d.last }
            );
        }

        this.lastclass = null;
        this.classData.request({
            watch: {
                series:  panelConfig.series,
                eventid: panelConfig.eventid,
                classcode: code,
                entrant: true,
                class:   true,
                champ:   true,
            }
        });
    }
}

customElements.define('announcer-panel', AnnouncerPanel);
