import { LitElement, html, css } from 'lit-element';
import { tablecss } from './styles.js';
import { t3 } from '../filters.js';

class ProTimerBox extends LitElement {

  static get properties() {
    return {
      timedata: { type: Object },
    };
  }

  static get styles() {
    return [ tablecss, css`
      td {
        text-align: center;
        vertical-align: middle;
        height: 3rem;
        font-size: 110%;
      }
      .RL { color: red; }
      .NS { color: blue; }
      .raw { font-size: 200%; }
    ` ]
  }

  render() {
    if (!this.timedata) return html`
        <div>Waiting for data</div>
    `;

    function trow(e) {
        return html`
            <tr>
            <td class='reaction ${e.status}'>${t3(e.reaction)}</td>
            <td class='sixty ${e.status}'>${t3(e.sixty)}</td>
            <td class='raw ${e.status}'>${e.raw != 'NaN' ? t3(e.raw) : ''}</td>
            </tr>
        `;
    }

    return html`
        <!-- timer -->
        <table>
        <tbody>
        ${this.timedata.map(r => trow(r))}
        </tbody>
        </table>`;
  }
}

customElements.define('pro-timer-box', ProTimerBox);
