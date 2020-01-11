import { LitElement, html, css } from 'lit-element';

// These are the elements needed by this element.
import '@polymer/paper-tabs/paper-tabs.js';
import '@polymer/paper-tabs/paper-tab.js';
import '@polymer/paper-listbox/paper-listbox.js';
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
          appTitle:  { type: String },
          dataSource: { type: Object },
          entrant:   { type: Object },
          cls:       { type: Object },
          champ:     { type: Object },
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
          `
        ];
    }

    render() {
        // Anything that's related to rendering should be done in here.
        return html`
          <!-- Main content -->
            <div class='outer'>
            <div class='col1'>
                <timer-box .time="${this.timer}"></timer-box>
                <runorder-table .order="${this.runorder}"></runorder-table>

                <div id='classtabs'>
                    <paper-tabs selected="1" @selected-changed="${(e) => this.cselected = e.target.selected}">
                    <paper-tab>2nd Last</paper-tab>
                    <paper-tab>Last</paper-tab>
                    <paper-tab>Next</paper-tab>
                    </paper-tabs>

                    <iron-pages .selected="${this.cselected}">
                        <div></div>
                        <div class='panel'>
                            <entrant-table .entrant="${this.entrant}"></entrant-table>
                            <class-table .cls="${this.cls}"></class-table>
                            <champ-table .champ="${this.champ}"></champ-table>
                        </div>
                        <div class='panel'>
                            <class-table .cls="${this.next ? this.next.class : undefined}"></class-table>
                            <champ-table .champ="${this.next ? this.next.champ: undefined}"></champ-table>
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
        this.dataSource = new DataSource(
            panelConfig.wsurl,
            function(d) {
                if ("entrant" in d) me.entrant = d.entrant;
                if ("class" in d)   me.cls     = d.class;
                if ("champ" in d)   me.champ   = d.champ;
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
}

customElements.define('announcer-panel', AnnouncerPanel);
