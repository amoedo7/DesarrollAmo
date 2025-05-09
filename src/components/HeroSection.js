import React from 'react';

const HeroSection = () => {
  return (
    <section className="min-h-screen flex flex-col justify-center items-center text-center px-6 bg-gradient-to-br from-blue-100/50 to-white dark:from-gray-900 dark:to-gray-800 backdrop-blur-lg">
      <h1 className="text-5xl md:text-7xl font-extrabold mb-4 text-blue-700 dark:text-blue-300 tracking-tight drop-shadow-lg">
        Desarroll<span className="text-pink-500">AMO</span>.
      </h1>

      <h2 className="text-2xl md:text-3xl font-medium mb-6 text-gray-700 dark:text-gray-200">
        Tu aliado humano para automatizar, crear y lanzar ideas con inteligencia artificial.
      </h2>

      <p className="text-md md:text-lg max-w-3xl mb-10 text-gray-600 dark:text-gray-400 leading-relaxed">
        No tenés que saber programar. Desde logos, videos y hojas de cálculo hasta flujos completos en n8n — yo conecto tu idea con la IA y la hago realidad.
      </p>

      <a
        href="https://instagram.com/amoedojuan"
        target="_blank"
        rel="noopener noreferrer"
        className="relative px-8 py-4 bg-pink-500 text-white rounded-full text-lg font-semibold shadow-md hover:shadow-2xl transition duration-300 hover:bg-pink-600"
      >
        ✨ Hablemos por Instagram
        <span className="absolute inset-0 rounded-full bg-pink-400 opacity-30 blur-lg animate-pulse -z-10"></span>
      </a>
    </section>
  );
};

export default HeroSection;
