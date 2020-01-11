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

class UserPanel extends LitElement {
    static get properties() {
        return {
            prev:     { type: Object },
            last:     { type: Object },
            next:     { type: Object },
            selected: { type: Number },
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
        <div class='appbar'>
        <paper-dropdown-menu no-animations no-label-float>
            <paper-listbox slot="dropdown-content" class="dropdown-content" selected="0" @selected-changed="${this.classChange}">
              <paper-item>All</paper-item>
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
            <div class='panel'>
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
        var select = {
            watch: {
                series:  panelConfig.series,
                eventid: panelConfig.eventid,
                entrant: true,
                class:   true,
                champ:   true,
                next:    true,
                topnet:  true,
                topraw:  true,
            }
        };

        this.dataSource.request(select);
    }


    constructor() {
        super();
        var me = this;
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
            }
        );
    }
}

customElements.define('user-panel', UserPanel);
