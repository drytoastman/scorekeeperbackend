import { LitElement, html, css } from 'lit-element';
import { tablecss } from './styles.js';

class TimerBox extends LitElement {

  static get properties() {
    return {
      time: { type: Number },
    };
  }

  static get styles() {
    return [ tablecss, css`
      td.timer {
        font-size: 300%;
        text-align: center;
      }
    ` ]
  }

  render() {
    return html`
        <!-- timer -->
        <table>
        <tbody>
        <tr class='head'><th colspan='6'>Timer</th></tr>
        <tr><td class='timer'>${this.time}</td></tr>
        </tbody>
        </table>`;
  }
}

customElements.define('timer-box', TimerBox);
