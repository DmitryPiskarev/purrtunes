export async function POST(req: Request) {
  try {
    // Attempt to parse the JSON request body
    const { userId, message, walletAddress } = await req.json();

    // Check if both userId and message are provided
    if (!userId || !message) {
      return new Response(
        JSON.stringify({ error: 'User ID and message are required' }),
        { status: 400 }
      );
    }

    console.log("Received user ID:", userId);
    console.log("Received message:", message);
    console.log("Received walletAddress:", walletAddress);

    const botToken = process.env.NEXT_PUBLIC_TG_ID;
    const url = `https://api.telegram.org/bot${botToken}/sendMessage`;

    const response = await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: userId,
        text: message,
        parse_mode: 'Markdown',
        reply_markup: JSON.stringify({
          inline_keyboard: [
            [
              {
                text: '✅ Approve Address',
                callback_data: `approve_${walletAddress}` // Pass wallet address in callback
              }
            ]
          ]
        })
      }),
    });


    const data = await response.json();

    if (data.ok) {
      return new Response(
        JSON.stringify({ success: true, message: 'Message sent successfully' }),
        { status: 200 }
      );
    } else {
      return new Response(
        JSON.stringify({ error: 'Failed to send message', details: data }),
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('Error processing the request:', error);

    return new Response(
      JSON.stringify({ error: 'Invalid JSON or missing body' }),
      { status: 400 }
    );
  }
}
