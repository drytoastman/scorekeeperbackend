import { LitElement, html, css } from 'lit-element';

// These are the elements needed by this element.
import '@polymer/paper-tabs/paper-tabs.js';
import '@polymer/paper-tabs/paper-tab.js';
import '@polymer/paper-dropdown-menu/paper-dropdown-menu.js';
import '@polymer/paper-listbox/paper-listbox.js';
import '@polymer/paper-item/paper-item.js';
import '@polymer/iron-pages/iron-pages.js';

import { DataSource } from '../datasource.js';
import './entrant-table.js';
import './class-table.js';
import './champ-table.js';
import './toptimes-table.js';
import './data-selector.js';

class LivePanel extends LitElement {
    static get properties() {
        return {
            appTitle: { type: String },
            dataSource: { type: Object },
            entrant:  { type: Object },
            cls:      { type: Object },
            champ:    { type: Object },
            selected: { type: Number }
        };
    }

    static get styles() {
        return [
          css`
            :host {
            }

            .panel {
                display: flex;
                flex-wrap: wrap;
            }

            .panel * {
                margin: 2px;
                flex-grow: 1;
            }

            .appbar {
                display: flex;
            }

            paper-dropdown-menu {
                width: 4rem;
                vertical-align: top;
                margin-top: 5px;
                --paper-input-container-color: white;
            }

            paper-tabs {
                flex-grow: 1;
            }
          `
        ];
    }

    render() {
        // Anything that's related to rendering should be done in here.
        return html`
        <!-- <data-selector .dataSource="${this.dataSource}"></data-selector> -->

        <div class='appbar'>
        <paper-dropdown-menu no-animations no-label-float>
            <paper-listbox slot="dropdown-content" class="dropdown-content" selected="0" @selected-changed="${this.classChange}">
              <paper-item>All</paper-item>
              <paper-item>AS</paper-item>
              <paper-item>BS</paper-item>
              <paper-item>NS4</paper-item>
              <paper-item>NS6</paper-item>
            </paper-listbox>
        </paper-dropdown-menu>

        <paper-tabs selected="1" @selected-changed="${(e) => this.selected = e.target.selected}">
        <paper-tab>Prev</paper-tab>
        <paper-tab>Last</paper-tab>
        <paper-tab>Next</paper-tab>
        <paper-tab>Index</paper-tab>
        <paper-tab>Raw</paper-tab>
        </paper-tabs>
        </div>

       <iron-pages .selected="${this.selected}">
            <div id='prevpanel' class='panel'></div>
            <div id='curpanel'  class='panel'>
                <entrant-table .entrant="${this.entrant}"></entrant-table>
                <class-table .cls="${this.cls}"></class-table>
                <champ-table .champ="${this.champ}"></champ-table>
            </div>
            <div id='nextpanel' class='panel'>
                <class-table .cls="${this.next ? this.next.class : undefined}"></class-table>
                <champ-table .champ="${this.next ? this.next.champ: undefined}"></champ-table>
            </div>
            <div class='panel'>
                <toptimes-table .order="${this.topnet}" type="Index"></toptimes-table>
            </div>
            <div class='panel'>
                <toptimes-table .order="${this.topraw}" type="Raw"></toptimes-table>
            </div>
        </iron-pages>
        `;
    }

    classChange(e) {
        var idx = e.target.selected;
        console.log(`classchange ${e.target.children[idx].textContent}`);
        this.series = 'nwr2019';
        this.eventid = '3721546e-1ee0-11e9-95b4-0242ac170003';
        var select = {
            series: this.series,
            eventid: this.eventid,
            watch: {
                timer: {},
                protimer: {},
                results: [
                  {
                    eventid: this.eventid,
                    entrant: true,
                    class: true,
                    champ: true,
                    next: true,
                    topnet: true,
                    topraw: true,
                  },
                ]
            }
        };

        this.dataSource.request(select);
    }


    constructor() {
        super();
        var me = this;
        this.dataSource = new DataSource(
            function(d) {
                if ("entrant" in d) me.entrant = d.entrant;
                if ("class" in d)   me.cls     = d.class;
                if ("champ" in d)   me.champ   = d.champ;
                if ("next" in d)    me.next    = d.next;
                if ("topnet" in d)  me.topnet  = d.topnet;
                if ("topraw" in d)  me.topraw  = d.topraw;
            }
        );
    }
}

customElements.define('live-panel', LivePanel);
