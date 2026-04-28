const dados = [
    { h: '23h', v: 14 }, { h: '01h', v: 20 }, { h: '02h', v: 22 },
    { h: '03h', v: 35 }, { h: '04h', v: 29 }, { h: '05h', v: 33 },
    { h: '06h', v: 34 }, { h: '07h', v: 32 }, { h: '08h', v: 10 },
    { h: '09h', v: 18 }, { h: '10h', v: 28 }
];

const max = Math.max(...dados.map(d => d.v));
const area = document.getElementById('chartArea');

dados.forEach(d => {
    const pct = (d.v / max) * 100;
    area.innerHTML += `
        <div class="bar-wrap">
            <div class="bar" style="height:${pct}%"></div>
            <span class="bar-label">${d.h}</span>
        </div>`;
});