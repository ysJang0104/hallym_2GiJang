import React from 'react';
import { Link } from 'react-router-dom';
import PropTypes from 'prop-types';

function FeatureCard({ title, description, link, linkText }) {
  return (
    <div className="feature-card">
      <h3>{title}</h3>
      <p>{description}</p>
      <Link to={link} className="btn-secondary">{linkText}</Link>
    </div>
  );
}

FeatureCard.propTypes = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  link: PropTypes.string.isRequired,
  linkText: PropTypes.string.isRequired,
};

export default React.memo(FeatureCard);
