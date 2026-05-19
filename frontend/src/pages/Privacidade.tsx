export default function Privacidade() {
  return (
    <div className="min-h-screen bg-white text-gray-800 px-6 py-12">
      <div className="max-w-2xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Política de Privacidade</h1>
          <p className="text-gray-500 mt-2 text-sm">Última atualização: maio de 2026</p>
        </div>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-900">1. Sobre esta política</h2>
          <p className="text-gray-700 leading-relaxed">
            Esta Política de Privacidade descreve como o escritório de advocacia <strong>Q&S Advocacia</strong>,
            por meio do sistema <strong>Juri Q&S</strong>, coleta, utiliza e protege as informações
            de pessoas jurídicas identificadas em documentos judiciais públicos para fins de
            oferta de serviços jurídicos trabalhistas.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-900">2. Dados coletados</h2>
          <p className="text-gray-700 leading-relaxed">
            Os dados processados por este sistema são obtidos exclusivamente de documentos
            judiciais públicos disponíveis em portais de tribunais trabalhistas, e incluem:
          </p>
          <ul className="list-disc pl-6 text-gray-700 space-y-1">
            <li>Razão social e CNPJ da empresa (parte reclamada)</li>
            <li>Número do processo e vara judicial</li>
            <li>Data e tipo de audiência</li>
            <li>Valor da causa</li>
            <li>Telefone comercial (obtido via consulta pública de CNPJ)</li>
          </ul>
          <p className="text-gray-700 leading-relaxed">
            Não coletamos dados de pessoas físicas além do nome do reclamante, que consta
            nos documentos públicos do processo.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-900">3. Finalidade do uso dos dados</h2>
          <p className="text-gray-700 leading-relaxed">
            Os dados são utilizados exclusivamente para:
          </p>
          <ul className="list-disc pl-6 text-gray-700 space-y-1">
            <li>Identificar empresas com demandas trabalhistas em andamento</li>
            <li>Enviar uma mensagem via WhatsApp oferecendo serviços de assessoria jurídica trabalhista</li>
            <li>Gerenciar o relacionamento com potenciais clientes do escritório</li>
          </ul>
          <p className="text-gray-700 leading-relaxed">
            As mensagens enviadas são de natureza comercial e informativa. O destinatário pode,
            a qualquer momento, solicitar a remoção de seus dados respondendo à mensagem recebida.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-900">4. Compartilhamento de dados</h2>
          <p className="text-gray-700 leading-relaxed">
            As informações coletadas <strong>não são compartilhadas, vendidas ou repassadas</strong> a
            terceiros. O acesso é restrito aos advogados e colaboradores autorizados do escritório Q&S Advocacia.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-900">5. Retenção dos dados</h2>
          <p className="text-gray-700 leading-relaxed">
            Os dados são mantidos enquanto houver interesse legítimo do escritório em manter contato
            com a empresa ou enquanto o processo judicial estiver em andamento. Após esse período,
            os dados são excluídos do sistema.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-900">6. Canal de comunicação — WhatsApp</h2>
          <p className="text-gray-700 leading-relaxed">
            O envio de mensagens via WhatsApp é realizado através da plataforma oficial
            <strong> WhatsApp Business API</strong>, operada pela Meta Platforms, Inc.
            As mensagens utilizam templates pré-aprovados pela Meta e são enviadas por número
            de telefone comercial registrado e verificado.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-900">7. Seus direitos</h2>
          <p className="text-gray-700 leading-relaxed">
            De acordo com a Lei Geral de Proteção de Dados (LGPD — Lei nº 13.709/2018),
            você tem o direito de:
          </p>
          <ul className="list-disc pl-6 text-gray-700 space-y-1">
            <li>Solicitar acesso aos dados que temos sobre sua empresa</li>
            <li>Solicitar a correção de dados incorretos</li>
            <li>Solicitar a exclusão dos seus dados do sistema</li>
            <li>Opor-se ao uso dos seus dados para contato comercial</li>
          </ul>
          <p className="text-gray-700 leading-relaxed">
            Para exercer qualquer desses direitos, entre em contato pelo e-mail ou WhatsApp
            informados na mensagem recebida.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-gray-900">8. Contato</h2>
          <p className="text-gray-700 leading-relaxed">
            Dúvidas sobre esta política podem ser encaminhadas ao escritório Q&S Advocacia
            diretamente pelo WhatsApp ou pelo e-mail de contato do escritório.
          </p>
        </section>

        <div className="border-t pt-6 text-gray-400 text-xs">
          Q&S Advocacia · Sistema Juri Q&S · Esta política pode ser atualizada periodicamente.
        </div>
      </div>
    </div>
  );
}
