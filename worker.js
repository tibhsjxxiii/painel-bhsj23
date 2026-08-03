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
 * 5. Volte para o Worker, vá em "Settings" → "Variables and Secrets", adicione DUAS variáveis secretas:
 *      ANTHROPIC_API_KEY  → sua chave (crie uma em https://console.anthropic.com/settings/keys)
 *      DASHBOARD_SECRET   → uma senha qualquer só sua, ex: "bhsj-2026-x7k9" (invente uma)
 * 6. Troque ALLOWED_ORIGIN abaixo pelo domínio onde o painel vai ficar publicado
 *    (ex: "https://seusite.netlify.app") — evita que outros sites usem seu proxy
 * 7. Copie a URL do seu Worker (algo como https://bhsjxxiii-ia.SEU-USUARIO.workers.dev)
 * 8. Gere o painel com:
 *    python gerar_dashboard.py planilha.ods --proxy-url "https://SEU-WORKER.workers.dev" --proxy-secret "a MESMA senha do passo 5"
 * 9. (Recomendado) Limite de uso: no painel do Worker, vá em "Triggers" →
 *    "Add Rate Limiting Rule" e defina algo como "60 requisições por minuto
 *    por IP" — protege contra uso abusivo mesmo com o segredo configurado.
 *
 * Segurança: mesmo que alguém descubra a URL do Worker, sem o DASHBOARD_SECRET
 * correto (que só existe dentro do painel gerado) as requisições são recusadas.
 * O CORS restrito impede que outros sites façam chamadas ao seu proxy pelo navegador.
 */

const ALLOWED_ORIGIN = '*'; // troque para o domínio final do seu painel, ex: 'https://seusite.netlify.app'

export default {
  async fetch(request, env) {
    const corsHeaders = {
      'Access-Control-Allow-Origin': ALLOWED_ORIGIN,
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, X-Dashboard-Secret',
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

    // shared-secret check: blocks anyone who doesn't have the dashboard's secret,
    // even if they discover the Worker URL
    if (env.DASHBOARD_SECRET) {
      const provided = request.headers.get('X-Dashboard-Secret') || '';
      if (provided !== env.DASHBOARD_SECRET) {
        return new Response(JSON.stringify({ error: 'unauthorized' }), {
          status: 401,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }
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
