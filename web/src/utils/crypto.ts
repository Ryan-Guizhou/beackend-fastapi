
/**
 * Base64 to ArrayBuffer
 */
function base64ToUint8Array(base64: string): Uint8Array {
  const binaryString = window.atob(base64)
  const len = binaryString.length
  const bytes = new Uint8Array(len)
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i)
  }
  return bytes
}

/**
 * ArrayBuffer to Base64URL
 */
function arrayBufferToBase64Url(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return window.btoa(binary)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '')
}

/**
 * RSA Encryption using Web Crypto API (RSA-OAEP-SHA256)
 */
export async function encryptRSA(publicKeyBase64: string, plainText: string): Promise<string> {
  const pemHeader = '-----BEGIN PUBLIC KEY-----'
  const pemFooter = '-----END PUBLIC KEY-----'
  
  // Clean the key if it's wrapped in PEM headers
  let cleanKey = publicKeyBase64
    .replace(pemHeader, '')
    .replace(pemFooter, '')
    .replace(/\s/g, '')

  const binaryKey = base64ToUint8Array(cleanKey)
  
  const publicKey = await window.crypto.subtle.importKey(
    'spki',
    binaryKey,
    {
      name: 'RSA-OAEP',
      hash: 'SHA-256',
    },
    false,
    ['encrypt']
  )

  const encrypted = await window.crypto.subtle.encrypt(
    {
      name: 'RSA-OAEP',
    },
    publicKey,
    new TextEncoder().encode(plainText)
  )

  return arrayBufferToBase64Url(encrypted)
}

/**
 * AES-GCM Encryption using Web Crypto API
 */
export async function encryptAES(data: any, keyBase64: string): Promise<{ nonce: string; cipherText: string }> {
  const key = await window.crypto.subtle.importKey(
    'raw',
    base64ToUint8Array(keyBase64),
    { name: 'AES-GCM' },
    false,
    ['encrypt']
  )

  const nonce = window.crypto.getRandomValues(new Uint8Array(12))
  const src = typeof data === 'string' ? data : JSON.stringify(data)
  
  const encrypted = await window.crypto.subtle.encrypt(
    {
      name: 'AES-GCM',
      iv: nonce,
    },
    key,
    new TextEncoder().encode(src)
  )

  return {
    nonce: arrayBufferToBase64Url(nonce.buffer),
    cipherText: arrayBufferToBase64Url(encrypted),
  }
}

/**
 * AES-GCM Decryption using Web Crypto API
 */
export async function decryptAES(cipherTextBase64: string, keyBase64: string, nonceBase64: string): Promise<string> {
  const key = await window.crypto.subtle.importKey(
    'raw',
    base64ToUint8Array(keyBase64),
    { name: 'AES-GCM' },
    false,
    ['decrypt']
  )

  const decrypted = await window.crypto.subtle.decrypt(
    {
      name: 'AES-GCM',
      iv: base64ToUint8Array(nonceBase64),
    },
    key,
    base64ToUint8Array(cipherTextBase64)
  )

  return new TextDecoder().decode(decrypted)
}
