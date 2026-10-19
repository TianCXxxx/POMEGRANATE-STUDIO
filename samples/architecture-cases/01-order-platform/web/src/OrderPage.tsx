import React, { useState } from 'react';
import { submitRequest } from './api';
export function OrderPage() {
  const [result, setResult] = useState('');
  async function handleSubmit() {
    const response = await submitRequest({reference: 'demo-1001', amount: 120});
    setResult(JSON.stringify(response));
  }
  return <section><button onClick={handleSubmit}>提交请求</button><pre>{result}</pre></section>;
}
