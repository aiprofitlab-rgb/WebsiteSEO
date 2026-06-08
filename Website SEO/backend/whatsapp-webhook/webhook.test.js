const express = require('express');
const request = require('supertest');
const webhookRouter = require('./webhook');

describe('WhatsApp Webhook Integration', () => {
  let app;

  beforeEach(() => {
    app = express();
    process.env.VERIFY_TOKEN = 'meatyhamhock';
    app.use('/webhook', webhookRouter);
  });

  describe('GET /webhook (Verification)', () => {
    it('should return 200 and challenge code on valid verification', async () => {
      const response = await request(app)
        .get('/webhook?hub.mode=subscribe&hub.verify_token=meatyhamhock&hub.challenge=1158201444');
      
      expect(response.status).toBe(200);
      expect(response.text).toBe('1158201444');
    });

    it('should return 403 on invalid verification token', async () => {
      const response = await request(app)
        .get('/webhook?hub.mode=subscribe&hub.verify_token=wrongtoken&hub.challenge=1158201444');
      
      expect(response.status).toBe(403);
    });

    it('should return 400 on missing parameters', async () => {
      const response = await request(app).get('/webhook');
      expect(response.status).toBe(400);
    });
  });

  describe('POST /webhook (Message Processing)', () => {
    it('should return 200 on valid message payload', async () => {
      const payload = {
        object: 'whatsapp_business_account',
        entry: [
          {
            id: 'WHATSAPP_BUSINESS_ACCOUNT_ID',
            changes: [
              {
                value: {
                  messaging_product: 'whatsapp',
                  messages: [
                    {
                      from: '1234567890',
                      id: 'wamid.ID',
                      timestamp: '1611111111',
                      type: 'text',
                      text: {
                        body: 'Hello World'
                      }
                    }
                  ]
                },
                field: 'messages'
              }
            ]
          }
        ]
      };

      const response = await request(app)
        .post('/webhook')
        .send(payload);

      expect(response.status).toBe(200);
    });

    it('should handle null strings and missing fields gracefully without crashing', async () => {
      const payload = {
        object: 'whatsapp_business_account',
        entry: [
          {
            changes: [
              {
                value: {
                  messages: [
                    {
                      type: 'text',
                      text: null // missing body, null text object
                    }
                  ]
                }
              }
            ]
          }
        ]
      };

      const response = await request(app)
        .post('/webhook')
        .send(payload);

      expect(response.status).toBe(200); // Should just ignore and return 200
    });

    it('should return 404 if object is not whatsapp_business_account', async () => {
      const payload = {
        object: 'page',
        entry: []
      };

      const response = await request(app)
        .post('/webhook')
        .send(payload);

      expect(response.status).toBe(404);
    });

    it('should return 400 on empty payload', async () => {
      const response = await request(app)
        .post('/webhook')
        .send({});

      expect(response.status).toBe(400);
    });

    it('should return 400 if object is missing', async () => {
      const payload = {
        entry: []
      };

      const response = await request(app)
        .post('/webhook')
        .send(payload);

      expect(response.status).toBe(400);
    });
  });
});
