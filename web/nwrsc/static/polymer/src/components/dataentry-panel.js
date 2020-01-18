import { LitElement, html, css } from 'lit-element';

import { DataSource } from '../datasource.js';
import './entrant-table.js';
import './class-table.js';
import './champ-table.js';

class DataEntryPanel extends LitElement {
    static get properties() {
        return {
            last: { type: Object },
        };
    }

    static get styles() {
        return [
          css`
            entrant-table, class-table, champ-table {
                display: block;
                font-size: 90%;
                margin-bottom: 1rem;
            }
          `
        ];
    }

    render() {
        return html`
        <div class='panel'>
            <entrant-table .entrant="${this.last ? this.last.entrant : undefined}"></entrant-table>
            <class-table       .cls="${this.last ? this.last.class   : undefined}" noindexcol=true nodiff1col=true></class-table>
            <champ-table     .champ="${this.last ? this.last.champ   : undefined}"></champ-table>
        </div>
        `;
    }

    constructor() {
        super();
        var me = this;
        this.dataSource = new DataSource(
            panelConfig.wsurl,
            function(d) {
                if ("last" in d) me.last = d.last;
            }
        );

        this.dataSource.request({
            watch: {
                series:  panelConfig.series,
                eventid: panelConfig.eventid,
                entrant: true,
                class:   true,
                champ:   true
            }
        });

        // easiest way to remove the default parent body margin
        document.body.style.margin = "0";
    }
}

customElements.define('dataentry-panel', DataEntryPanel);
