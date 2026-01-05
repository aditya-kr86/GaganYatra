import { Shield } from 'lucide-react';
import Navbar from '../components/common/Navbar';
import Footer from '../components/common/Footer';
import './StaticPages.css';

const PrivacyPage = () => {
  const lastUpdated = 'December 27, 2025';

  const sections = [
    {
      title: '1. Introduction',
      content: `FlightBooker ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your personal information when you use our website, mobile applications, and services.

By using our services, you consent to the data practices described in this policy. We encourage you to read this Privacy Policy carefully and contact us if you have any questions.`
    },
    {
      title: '2. Information We Collect',
      content: `We collect information in several ways:

**Personal Information You Provide:**
• Name, email address, phone number during registration
• Passport details, date of birth for flight bookings
• Billing address and payment information
• Travel preferences and frequent flyer numbers
• Communication history with our support team

**Information Collected Automatically:**
• Device information (type, operating system, browser)
• IP address and location data
• Usage data (pages visited, features used, time spent)
• Cookies and similar tracking technologies

**Information from Third Parties:**
• Airlines (booking confirmations, flight status)
• Payment processors (transaction verification)
• Social media platforms (if you sign in using social accounts)`
    },
    {
      title: '3. How We Use Your Information',
      content: `We use the collected information for:

**Service Delivery:**
• Processing and managing flight bookings
• Sending booking confirmations and e-tickets
• Providing customer support and responding to inquiries
• Sending flight updates and travel alerts

**Personalization:**
• Customizing your experience based on preferences
• Recommending flights and destinations
• Remembering your search history and preferences

**Communication:**
• Sending promotional offers (with your consent)
• Notifying you of policy changes
• Providing newsletters and travel tips

**Analytics and Improvement:**
• Analyzing usage patterns to improve our services
• Conducting research and surveys
• Debugging and fixing issues

**Legal and Security:**
• Complying with legal obligations
• Preventing fraud and ensuring security
• Enforcing our terms and policies`
    },
    {
      title: '4. Information Sharing',
      content: `We may share your information with:

**Airlines and Travel Partners:**
Essential booking information is shared with airlines to complete your reservation. This includes passenger names, contact details, and travel documents.

**Service Providers:**
We work with third-party companies for payment processing, email delivery, customer support, and analytics. These providers are bound by confidentiality agreements.

**Legal Requirements:**
We may disclose information if required by law, court order, or government request, or to protect our rights and safety.

**Business Transfers:**
In case of merger, acquisition, or sale of assets, user information may be transferred to the new entity.

**We Never:**
• Sell your personal data to third parties for marketing
• Share your information with advertisers without consent
• Provide your data to unrelated companies`
    },
    {
      title: '5. Data Security',
      content: `We implement robust security measures:

• **Encryption:** All data transmissions are encrypted using TLS/SSL
• **Secure Storage:** Personal data is stored on secure, encrypted servers
• **Access Controls:** Only authorized personnel can access personal data
• **Regular Audits:** We conduct security assessments and penetration testing
• **PCI Compliance:** Payment information is handled per PCI-DSS standards

While we strive to protect your data, no method of transmission over the internet is 100% secure. We cannot guarantee absolute security but take all reasonable precautions.`
    },
    {
      title: '6. Cookies and Tracking',
      content: `We use cookies and similar technologies:

**Essential Cookies:**
Required for basic functionality like login sessions and security.

**Functional Cookies:**
Remember your preferences, language, and search history.

**Analytics Cookies:**
Help us understand how users interact with our platform (via Google Analytics, etc.).

**Marketing Cookies:**
Used for targeted advertising (only with your consent).

**Managing Cookies:**
You can control cookies through your browser settings. Disabling essential cookies may affect functionality. We respect "Do Not Track" browser signals.`
    },
    {
      title: '7. Your Rights',
      content: `You have the following rights regarding your data:

**Right to Access:**
Request a copy of personal data we hold about you.

**Right to Rectification:**
Update or correct inaccurate information in your account.

**Right to Deletion:**
Request deletion of your personal data (subject to legal retention requirements).

**Right to Portability:**
Receive your data in a structured, machine-readable format.

**Right to Object:**
Opt-out of marketing communications and certain data processing.

**Right to Restrict:**
Limit how we process your data in certain circumstances.

To exercise these rights, contact us at privacy@flightbooker.com. We will respond within 30 days.`
    },
    {
      title: '8. Data Retention',
      content: `We retain your data for as follows:

• **Account Information:** As long as your account is active
• **Booking Records:** 7 years (legal/tax requirements)
• **Communication Logs:** 3 years after last interaction
• **Analytics Data:** 2 years (anonymized)
• **Marketing Preferences:** Until you opt-out

Upon account deletion request, we will remove or anonymize your data within 30 days, except where retention is required by law.`
    },
    {
      title: '9. Children\'s Privacy',
      content: `Our services are not intended for children under 13. We do not knowingly collect personal information from children under 13. If you believe we have collected such information, please contact us immediately.

For bookings involving minors, a parent or guardian must provide consent and be responsible for the accuracy of information provided.`
    },
    {
      title: '10. International Transfers',
      content: `Your information may be transferred to and processed in countries other than your own. We ensure appropriate safeguards are in place:

• Standard contractual clauses approved by regulators
• Data processing agreements with partners
• Compliance with applicable data protection laws

By using our services, you consent to international data transfers as described in this policy.`
    },
    {
      title: '11. Third-Party Links',
      content: `Our platform may contain links to third-party websites (airlines, hotels, etc.). We are not responsible for their privacy practices. We encourage you to review their privacy policies before providing any personal information.

We may also integrate third-party services (payment gateways, social media) that have their own privacy policies governing data use.`
    },
    {
      title: '12. Changes to This Policy',
      content: `We may update this Privacy Policy periodically. Changes will be posted on this page with an updated revision date. For significant changes, we will notify you via email or prominent notice on our platform.

Your continued use of our services after changes indicates acceptance of the updated policy. We encourage regular review of this page.`
    },
    {
      title: '13. Contact Us',
      content: `For privacy-related questions or to exercise your rights:

**Data Protection Officer:**
Email: privacy@flightbooker.com
Phone: 1800-XXX-XXXX

**Mailing Address:**
FlightBooker Privacy Team
Tech Park, Sector 126
Noida, UP 201303, India

**Grievance Redressal:**
If you have concerns about how we handle your data, please contact our Grievance Officer at grievance@flightbooker.com. We will address your concerns within 30 days.`
    }
  ];

  return (
    <>
      <Navbar />
      <div className="static-page privacy-page">
        <div className="static-hero">
          <div className="hero-content">
            <Shield size={48} />
            <h1>Privacy Policy</h1>
            <p>Your privacy is important to us. Learn how we protect your data.</p>
          </div>
        </div>

        <div className="static-container">
          <div className="legal-meta">
            <p><strong>Last Updated:</strong> {lastUpdated}</p>
            <p><strong>Effective Date:</strong> {lastUpdated}</p>
          </div>

          <div className="legal-intro">
            <p>
              At FlightBooker, we take your privacy seriously. This Privacy Policy describes 
              how we collect, use, and protect your personal information when you use our 
              flight booking platform. We are committed to transparency and giving you 
              control over your data.
            </p>
          </div>

          <div className="privacy-highlights">
            <h2>Key Highlights</h2>
            <div className="highlights-grid">
              <div className="highlight-card">
                <span className="highlight-icon">🔒</span>
                <h4>Secure Data</h4>
                <p>Your data is encrypted and protected with industry-standard security</p>
              </div>
              <div className="highlight-card">
                <span className="highlight-icon">🚫</span>
                <h4>No Data Selling</h4>
                <p>We never sell your personal information to third parties</p>
              </div>
              <div className="highlight-card">
                <span className="highlight-icon">⚙️</span>
                <h4>Your Control</h4>
                <p>Access, modify, or delete your data anytime</p>
              </div>
              <div className="highlight-card">
                <span className="highlight-icon">📧</span>
                <h4>Opt-Out</h4>
                <p>Easily unsubscribe from marketing communications</p>
              </div>
            </div>
          </div>

          <div className="legal-sections">
            {sections.map((section, index) => (
              <div key={index} className="legal-section">
                <h2>{section.title}</h2>
                <div className="section-content">
                  {section.content.split('\n\n').map((paragraph, pIndex) => (
                    <p key={pIndex}>{paragraph}</p>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="legal-footer">
            <p>
              By using FlightBooker's services, you acknowledge that you have read and 
              understood this Privacy Policy. If you have any questions or concerns, 
              please contact our Privacy Team at privacy@flightbooker.com.
            </p>
          </div>
        </div>
      </div>
      <Footer />
    </>
  );
};

export default PrivacyPage;
