import { LitElement, html, css } from 'lit-element';
import { t3 } from '../filters.js';
import { tablecss } from './styles.js';

class RunOrderTable extends LitElement {

  static get properties() {
    return {
      order: { type: Object },
      small: { type: Boolean },
    };
  }

  static get styles() {
    return [ tablecss, css`
            td {
                /* for overflow to work */
                max-width: 9rem;
            }
     ` ]
  }


  render() {
    if (!this.order) {
        return html``;
    }

    var small = this.small;

    function erow(e) {
        return html`
            <tr>
            <td class='name limit'>${e.firstname} ${e.lastname}</td>
            ${small ? '' : html`<td class='limit'>${e.year} ${e.model} ${e.color}</td>`}
            <td>${e.classcode}</td>
            <td>${e.bestrun ? html`${t3(e.bestrun.raw)} (${e.bestrun.cones}, ${e.bestrun.gates})` : ''}</td>
            <td>${e.position}</td>
            <td>${t3(e.diffn)}</td>
            </tr>
        `;
    }

    return html`
        <!-- next to finish table -->
        <table class='runorder'>
        <tbody>
        <tr class='head'><th colspan='${small ? '5':'6'}'>Next To Finish</th></tr>
        <tr class='subhead'>
        <th>Name</th>
        ${small ? '' : html`<th>Car</th>`}
        <th>Class</th>
        <th>Best</th>
        <th>Pos</th>
        <th>Need</th>
        </tr>
        ${this.order.next.map(e => erow(e))}
        </tbody>
        </table>`;
  }
}

customElements.define('runorder-table', RunOrderTable);
