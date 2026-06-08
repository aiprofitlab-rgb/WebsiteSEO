const express = require('express');

const router = express.Router();
router.use(express.json());

// Webhook verification endpoint (GET)
router.get('/', (req, res) => {
  const mode = req.query['hub.mode'];
  const token = req.query['hub.verify_token'];
  const challenge = req.query['hub.challenge'];
  const VERIFY_TOKEN = process.env.VERIFY_TOKEN || 'YOUR_VERIFY_TOKEN';

  if (mode && token) {
    if (mode === 'subscribe' && token === VERIFY_TOKEN) {
      console.log('WEBHOOK_VERIFIED');
      return res.status(200).send(challenge);
    } else {
      return res.sendStatus(403);
    }
  }
  return res.sendStatus(400);
});

// Webhook message processor (POST)
router.post('/', (req, res) => {
  try {
    const body = req.body;

    if (!body || !body.object) {
      console.error('Invalid payload or missing object field');
      return res.sendStatus(400); // Bad Request
    }

    // Process WhatsApp messages
    if (body.object === 'whatsapp_business_account') {
      const entry = body.entry;

      if (entry && Array.isArray(entry)) {
        entry.forEach((ent) => {
          const changes = ent.changes;
          if (changes && Array.isArray(changes)) {
            changes.forEach((change) => {
              // Safety checks for nested properties
              const value = change.value;
              if (value && value.messages && Array.isArray(value.messages)) {
                value.messages.forEach((msg) => {
                  if (msg && msg.type === 'text' && msg.text && msg.text.body) {
                    console.log('Received message:', msg.text.body, 'from', msg.from);
                    // In a real app, process the message and trigger a response
                  } else {
                    console.log('Received non-text message or missing body:', msg);
                  }
                });
              } else if (value && value.statuses) {
                // Handling message statuses (sent, delivered, read)
                console.log('Received status update:', value.statuses);
              } else {
                console.log('No messages or statuses found in change value');
              }
            });
          }
        });
      }
      return res.sendStatus(200); // Acknowledge the event
    } else {
      // Return 404 if the object is not what we expect
      return res.sendStatus(404);
    }
  } catch (error) {
    console.error('Error processing webhook:', error.message);
    return res.sendStatus(500);
  }
});

module.exports = router;
