/**
 * Proxy de IA — Barco Hospital São João XXIII
 * =============================================
 * Roda no Cloudflare Workers (gratuito). Guarda sua chave da Anthropic em
 * segredo no servidor e repassa perguntas do painel para o Claude, para que
 * o Assistente de Dados consiga responder QUALQUER pergunta, não só as
 * reconhecidas por padrão.
 *
 * Como implantar (5 minutos, gratuito):
 * 1. Crie uma conta em https://dash.cloudflare.com/sign-up
 * 2. No painel, vá em "Workers & Pages" → "Create" → "Create Worker"
 * 3. Dê um nome (ex: bhsjxxiii-ia) e clique em "Deploy"
 * 4. Clique em "Edit code", apague tudo, cole o conteúdo deste arquivo, e clique em "Deploy"
 * 5. Volte para o Worker, vá em "Settings" → "Variables and Secrets"
 * 6. Adicione uma variável secreta chamada ANTHROPIC_API_KEY com sua chave
 *    (crie uma chave gratuita em https://console.anthropic.com/settings/keys)
 * 7. Copie a URL do seu Worker (algo como https://bhsjxxiii-ia.SEU-USUARIO.workers.dev)
 * 8. Cole essa URL na constante PROXY_URL no topo do template.html do painel
 *    e gere o dashboard novamente com gerar_dashboard.py
 */

const ALLOWED_ORIGINS = '*'; // pode restringir para o domínio do seu painel depois, ex: 'https://seusite.netlify.app'

export default {
  async fetch(request, env) {
    const corsHeaders = {
      'Access-Control-Allow-Origin': ALLOWED_ORIGINS,
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    if (request.method !== 'POST') {
      return new Response(JSON.stringify({ error: 'Method not allowed' }), {
        status: 405,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    if (!env.ANTHROPIC_API_KEY) {
      return new Response(JSON.stringify({ error: 'ANTHROPIC_API_KEY não configurada no Worker' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    try {
      const body = await request.json();
      const question = (body.question || '').toString().slice(0, 1000);
      const context = body.context || {};

      if (!question) {
        return new Response(JSON.stringify({ error: 'Pergunta vazia' }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }

      const systemPrompt =
        'Você é o analista de dados interno do painel executivo do Barco Hospital São ' +
        'João XXIII, um barco hospital que realiza expedições médicas fluviais no ' +
        'Amazonas (Brasil). Responda com base APENAS nos dados JSON fornecidos abaixo ' +
        '— nunca invente números. Responda no mesmo idioma da pergunta da pessoa, de ' +
        'forma direta, executiva e objetiva, citando números quando relevante. Se a ' +
        'pergunta não puder ser respondida com os dados fornecidos, diga isso ' +
        'claramente em vez de inventar. Dados: ' + JSON.stringify(context);

      const anthropicResponse = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': env.ANTHROPIC_API_KEY,
          'anthropic-version': '2023-06-01',
        },
        body: JSON.stringify({
          model: 'claude-sonnet-4-6',
          max_tokens: 1024,
          system: systemPrompt,
          messages: [{ role: 'user', content: question }],
        }),
      });

      if (!anthropicResponse.ok) {
        const errText = await anthropicResponse.text();
        return new Response(JSON.stringify({ error: 'Erro da API Anthropic', detail: errText }), {
          status: anthropicResponse.status,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }

      const data = await anthropicResponse.json();
      const text = (data.content || [])
        .map((b) => b.text || '')
        .join('\n')
        .trim();

      return new Response(JSON.stringify({ answer: text || 'Sem resposta.' }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }
  },
};
