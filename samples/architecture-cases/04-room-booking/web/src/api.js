export async function getRooms() {
  const response = await fetch('http://localhost:8080/api/rooms');
  if (!response.ok) throw new Error('无法读取会议室');
  return response.json();
}

export async function getBookings() {
  const response = await fetch('http://localhost:8080/api/bookings');
  if (!response.ok) throw new Error('无法读取预约');
  return response.json();
}

export async function createBooking(booking) {
  const response = await fetch('http://localhost:8080/api/bookings', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(booking)
  });
  if (!response.ok) throw new Error((await response.json()).detail || '预约失败');
  return response.json();
}
