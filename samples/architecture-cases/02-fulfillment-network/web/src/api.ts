export interface RequestPayload { reference: string; amount: number }
export async function submitRequest(payload: RequestPayload) {
  const response = await fetch('http://localhost:8200/fulfillment', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  });
  if (!response.ok) throw new Error('请求失败');
  return response.json();
}
