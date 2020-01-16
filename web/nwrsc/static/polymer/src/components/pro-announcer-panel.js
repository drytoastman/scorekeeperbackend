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
import './pro-timer-box.js';


class ProAnnouncerPanel extends LitElement {

    static get properties() {
        return {
          leftimer:   { type: Object },
          leftorder:  { type: Object },
          left:       { type: Object },

          rightimer:  { type: Object },
          rightorder: { type: Object },
          right:      { type: Object },

          lastclass:  { type: Object },
          lastchamp:  { type: Object },
          specclass:  { type: Object },
          specchamp:  { type: Object },

          hack:       { type: Number },
          cselected:  { type: Number },
          tselected:  { type: Number }
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

            .colcenter {
                flex-grow: 1;
            }

            pro-timer-box, runorder-table {
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

            pro-timer-box, runorder-table, entrant-table {
                display: block;
                margin-bottom: 0.5rem;
            }
          `
        ];
    }

    render() {
        return html`
          <!-- Main content -->
            <div class='outer'>
            <div class='colleft'>
                <pro-timer-box .timedata="${this.lefttimer}"></pro-timer-box>
                <runorder-table   .order="${this.leftorder}" small="true"></runorder-table>
                <entrant-table  .entrant="${this.left}"></entrant-table>
            </div>

            <div class='colcenter'>
                <div id='classtabs'>
                    <paper-tabs selected="0" @selected-changed="${(e) => { this.cselected = e.target.selected}}">
                    <paper-tab>Last</paper-tab>
                    <paper-tab>By Class</paper-tab>
                    <paper-tab>Index</paper-tab>
                    <paper-tab>Raw</paper-tab>
                    </paper-tabs>

                    <iron-pages .selected="${this.cselected}">
                        <div class='panel'>
                            <class-table       .cls="${this.lastclass}"></class-table>
                            <champ-table     .champ="${this.lastchamp}"></champ-table>
                        </div>
                        <div class='panel'>
                            <paper-dropdown-menu no-animations no-label-float>
                            <paper-listbox slot="dropdown-content" class="dropdown-content" selected="0" @selected-changed="${this.classChange}">
                                <paper-item>Off</paper-item>
                                ${panelConfig.classcodes.map(code => html`<paper-item>${code}</paper-item>`)}
                            </paper-listbox>
                            </paper-dropdown-menu>

                            <class-table       .cls="${this.specclass}"></class-table>
                            <champ-table     .champ="${this.specchamp}"></champ-table>
                        </div>
                        <div class='panel'>
                                <toptimes-table .order="${this.topnet}" type="Index"></toptimes-table>
                        </div>
                        <div class='panel'>
                            <toptimes-table .order="${this.topraw}" type="Raw"></toptimes-table>
                        </div>
                    </iron-pages>
                </div>
            </div>

            <div class='colright'>
                <pro-timer-box .timedata="${this.righttimer}"></pro-timer-box>
                <runorder-table .order="${this.rightorder}" small="true"></runorder-table>
                <entrant-table .entrant="${this.right}"></entrant-table>
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
                    if (d.last.entrant.lastcourse > 1) {
                        me.right      = d.last.entrant;
                        me.rightorder = d.runorder;
                    } else {
                        me.left      = d.last.entrant;
                        me.leftorder = d.runorder;
                    }
                    me.lastclass = d.last.class;
                    me.lastchamp = d.last.champ;
                }
                if ("topnet" in d)  me.topnet  = d.topnet;
                if ("topraw" in d)  me.topraw  = d.topraw;
                if ("protimer" in d) {
                    me.lefttimer  = d.protimer.left;
                    me.righttimer = d.protimer.right;
                    me.hack = Math.random(); // this seems to force the updates above through
                }
            }
        );

        this.dataSource.request({
            watch: {
                series:  panelConfig.series,
                eventid: panelConfig.eventid,
                timer:   true,
                runorder: true,
                protimer: true,
                entrant: true,
                class:   true,
                champ:   true,
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
            this.specclass = null;
            this.specchamp = null;
            return;
        }

        var me = this;
        if (this.classData == null) {
            this.classData = new DataSource(
                panelConfig.wsurl,
                (d) => { 
                    if ("last" in d) {
                        me.specclass = d.last.class;
                        me.specchamp = d.last.champ;
                    }
                }
            );
        }

        this.specclass  = null;
        this.specchamp = null;
        this.classData.request({
            watch: {
                series:  panelConfig.series,
                eventid: panelConfig.eventid,
                classcode: code,
                class:   true,
                champ:   true,
            }
        });
    }
}

customElements.define('pro-announcer-panel', ProAnnouncerPanel);
