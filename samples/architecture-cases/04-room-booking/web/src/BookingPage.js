import { createBooking, getBookings, getRooms } from './api.js';

const form = document.querySelector('#booking-form');
const room = document.querySelector('#room');
const message = document.querySelector('#message');
const list = document.querySelector('#bookings');

async function refresh() {
  const rooms = await getRooms();
  room.replaceChildren(...rooms.map(item => new Option(`${item.name}（${item.seats} 人）`, item.id)));
  const bookings = await getBookings();
  list.replaceChildren(...bookings.map(item => {
    const row = document.createElement('li');
    row.textContent = `${item.booker}：${item.slot}（会议室 ${item.room_id}）`;
    return row;
  }));
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  try {
    await createBooking({ room_id: Number(room.value), booker: document.querySelector('#booker').value, slot: document.querySelector('#slot').value });
    message.textContent = '预约成功';
    await refresh();
  } catch (error) {
    message.textContent = error.message;
  }
});

refresh().catch(error => { message.textContent = error.message; });
