import { LitElement, html, css } from 'lit-element';

// These are the elements needed by this element.
import '@polymer/app-layout/app-drawer/app-drawer.js';
import '@polymer/paper-icon-button/paper-icon-button.js';
import '@polymer/paper-tabs/paper-tabs.js';
import '@polymer/paper-tabs/paper-tab.js';
import '@polymer/iron-icons/iron-icons.js';
import '@polymer/iron-pages/iron-pages.js';

import { DataSource } from '../datasource.js';
import './entrant-table.js';
import './class-table.js';
import './champ-table.js';

class AnnouncerPanel extends LitElement {
  static get properties() {
    return {
      appTitle: { type: String },
      _drawerOpened: { type: Boolean },
      dataSource: { type: Object },
      entrant: { type: Object },
      cls: { type: Object },
      champ: { type: Object },
      timer: { type: Number },
      selected: { type: Number }
    };
  }

  static get styles() {
    return [
      css`
        :host {
          display: block;

          --app-drawer-width: 256px;

          --app-primary-color: #E91E63;
          --app-secondary-color: #293237;
          --app-dark-text-color: var(--app-secondary-color);
          --app-light-text-color: white;
          --app-section-even-color: #f7f7f7;
          --app-section-odd-color: white;

          --app-drawer-background-color: var(--app-secondary-color);
          --app-drawer-text-color: var(--app-light-text-color);
          --app-drawer-selected-color: #78909C;

          --paper-tabs-selection-bar-color: #000;
          --paper-tab-ink: #000;

          --could-have-background: #EDD;
          --could-have-color: #E77;

          --improved-on-background: #EEF;
          --improved-on-color: #99E;

          --highlight-background: #DDD;

          --basecolor: #3f75a2;
          --basecolor10: #4683b6;
          --headerfill: var(--basecolor);
          --titlesfill: var(--basecolor10);
        }

        .drawer-list {
          box-sizing: border-box;
          width: 100%;
          height: 100%;
          padding: 24px;
          background: var(--app-drawer-background-color);
          position: relative;
        }

        .drawer-list > a {
          display: block;
          text-decoration: none;
          color: var(--app-drawer-text-color);
          line-height: 40px;
          padding: 0 24px;
        }

        .drawer-list > a[selected] {
          color: var(--app-drawer-selected-color);
        }

        .timer {
            font-size: 150%;
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
      <!-- Header -->

      <!-- Drawer content -->
      <app-drawer .opened="${this._drawerOpened}" @opened-changed="${this._drawerOpenedChanged}">
        <nav class="drawer-list">
          <a ?selected="${this._page === 'view1'}" href="/view1">View One</a>
          <a ?selected="${this._page === 'view2'}" href="/view2">View Two</a>
          <a ?selected="${this._page === 'view3'}" href="/view3">View Three</a>
        </nav>
      </app-drawer>

      <!-- Main content -->

        <paper-tabs @selected-changed="${this.tabchange}">
        <paper-icon-button icon="menu" @click="${this.drawerToggle}"></paper-icon-button>
        <paper-tab>Prev</paper-tab>
        <paper-tab>Last</paper-tab>
        <paper-tab>Next</paper-tab>
        <paper-tab>Index</paper-tab>
        <paper-tab>Raw</paper-tab>
        <!--<span class='timer'>${this.timer}</span> -->
        </paper-tabs>

        <iron-pages .selected="${this.selected}">
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
    `;
  }

  constructor() {
    super();
    var me = this;
    this.selected = 0;
    this.dataSource = new DataSource(
        function(d) {
            if ("entrant" in d) me.entrant = d.entrant;
            if ("class" in d)   me.cls     = d.class;
            if ("champ" in d)   me.champ   = d.champ;
            if ("next" in d)    me.next    = d.next;
            if ("timer" in d)   me.timer   = d.timer;
        }
    );

    this.dataSource.request( {
                series: 'nwr2019',
                watch: {
                    timer: {},
                    protimer: {},
                    results: [
                        {
                            eventid: '3721546e-1ee0-11e9-95b4-0242ac170003',
                            //classcode: 'NS4',
                            entrant: true,
                            class: true,
                            champ: true,
                            next: true,
                            runorder: true,
                        },
                    ]
                }
            });
  }

  drawerToggle(e) {
    this._drawerOpened = !this._drawerOpened;
  }

  tabchange(e) {
    this.selected = e.target.selected;
  }

  _drawerOpenedChanged(e) {
    this._drawerOpened = e.target.opened;
  }
}

customElements.define('announcer-panel', AnnouncerPanel);
