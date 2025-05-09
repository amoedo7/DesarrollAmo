import React from 'react';

const AboutSection = () => {
  return (
    <section className="py-24 px-6 bg-gradient-to-b from-white to-blue-50 dark:from-gray-900 dark:to-gray-800">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center gap-12">
        {/* Imagen con estilo */}
        <div className="md:w-1/3 flex justify-center">
          <div className="relative w-48 h-48 rounded-full overflow-hidden shadow-xl border-4 border-white dark:border-gray-700 hover:scale-105 transition-transform duration-300">
            <img
              src="https://i.imgur.com/DDdnPGd.png"
              alt="Juan Amoedo"
              className="w-full h-full object-cover"
            />
          </div>
        </div>

        {/* Texto */}
        <div className="md:w-2/3 text-center md:text-left">
          <h2 className="text-5xl font-extrabold mb-6 text-gray-800 dark:text-white tracking-tight">
            Hola, soy <span className="text-blue-600 dark:text-blue-300">Amoedo Juan</span>
          </h2>
          <p className="text-lg mb-4 text-gray-700 dark:text-gray-300 leading-relaxed">
            Llevo años explorando el mundo de la tecnología, pero siempre con un enfoque humano.
            En <span className="font-semibold text-blue-600 dark:text-blue-400">DesarrollAMO</span>,
            combinamos lo mejor de la inteligencia artificial con el toque personal que solo un humano puede dar.
          </p>
          <p className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed">
            No somos una gran corporación. Somos un equipo pequeño, ágil y apasionado que cree
            que la tecnología debe adaptarse a las personas, no al revés.
          </p>
        </div>
      </div>
    </section>
  );
};

export default AboutSection;
