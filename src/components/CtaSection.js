import React from 'react';

const CtaSection = () => {
  return (
    <section className="py-24 px-6 bg-gradient-to-r from-blue-500 to-pink-500">
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-4xl font-extrabold mb-6 text-white">
          ¿Listo para dar vida a tu idea?
        </h2>
        <p className="text-xl mb-8 text-blue-100">
          Cuéntanos sobre tu proyecto y lo haremos realidad con inteligencia artificial y un toque personal. 
          Aunque mi perfil en Instagram no refleje mi faceta como programador, es ahí donde ofrezco atención más cercana y personalizada.
        </p>
        <a 
          href="https://instagram.com/amoedojuan" 
          target="_blank" 
          rel="noopener noreferrer"
          className="inline-block px-8 py-4 bg-white text-blue-600 rounded-full hover:bg-gray-100 transition-colors text-lg font-bold shadow-lg hover:shadow-xl"
        >
          Hablemos de tu proyecto
        </a>
      </div>
    </section>
  );
};

export default CtaSection;
