import { FileText } from 'lucide-react';
import Navbar from '../components/common/Navbar';
import Footer from '../components/common/Footer';
import './StaticPages.css';

const TermsPage = () => {
  const lastUpdated = 'December 27, 2025';

  const sections = [
    {
      title: '1. Acceptance of Terms',
      content: `By accessing and using FlightBooker's website, mobile application, or any of our services, you acknowledge that you have read, understood, and agree to be bound by these Terms and Conditions. If you do not agree to these terms, please do not use our services.

These terms apply to all visitors, users, and others who access or use our platform. We reserve the right to update or modify these terms at any time without prior notice. Your continued use of our services after any such changes constitutes your acceptance of the new terms.`
    },
    {
      title: '2. User Registration and Accounts',
      content: `To access certain features of our platform, you may be required to create an account. When registering, you agree to:

• Provide accurate, current, and complete information
• Maintain and promptly update your account information
• Keep your password secure and confidential
• Accept responsibility for all activities under your account
• Notify us immediately of any unauthorized use

You must be at least 18 years old to create an account. Users under 18 may use our services only with parental or guardian supervision. We reserve the right to suspend or terminate accounts that violate these terms.`
    },
    {
      title: '3. Booking and Reservations',
      content: `When making a booking through FlightBooker:

• All bookings are subject to availability and confirmation
• Prices are dynamic and may change until payment is completed
• You must provide accurate passenger information matching government-issued ID
• Booking confirmations are sent via email and displayed in your account
• PNR (Passenger Name Record) serves as your unique booking reference

We act as an intermediary between you and the airlines. The actual contract of carriage is between you and the operating airline. Airline terms and conditions apply in addition to ours.`
    },
    {
      title: '4. Pricing and Payments',
      content: `Our pricing policy includes:

• All prices are displayed in Indian Rupees (INR) unless otherwise stated
• Displayed prices include applicable taxes, fees, and surcharges
• Dynamic pricing means fares may fluctuate based on demand and availability
• Payment must be completed to confirm your booking
• We accept credit cards, debit cards, UPI, net banking, and select wallets

Once payment is processed, your booking is confirmed. In case of payment failure, please contact your bank or try an alternative payment method. We are not responsible for payment processing delays caused by third-party payment providers.`
    },
    {
      title: '5. Cancellations and Refunds',
      content: `Cancellation policies:

• Free cancellation within 24 hours of booking (if departure is 7+ days away)
• After 24 hours, airline cancellation policies apply
• Cancellation fees vary by airline and fare type
• Refunds are processed within 7-10 business days
• Refund amounts depend on fare rules and time of cancellation

To cancel, visit "My Bookings" in your account or contact customer support. Some promotional or discounted fares may be non-refundable. In case of airline-initiated cancellations, you are entitled to a full refund or rebooking.`
    },
    {
      title: '6. Changes and Modifications',
      content: `Booking modifications:

• Date, time, and route changes are subject to airline policies
• Modification fees may apply in addition to fare differences
• Some fare types may not allow modifications
• Name corrections (minor spelling) may be possible before departure
• Complete name changes typically require cancellation and rebooking

To request modifications, contact our customer support with your PNR. Changes are subject to availability and the fare difference (if any) must be paid.`
    },
    {
      title: '7. Travel Documents and Check-in',
      content: `You are responsible for:

• Carrying valid government-issued photo identification
• Ensuring passport validity for international travel (6 months minimum)
• Obtaining necessary visas and travel permits
• Arriving at the airport with sufficient time before departure
• Completing web check-in or airport check-in as required

FlightBooker is not responsible for denied boarding due to improper documentation, late arrival, or failure to meet entry requirements of your destination.`
    },
    {
      title: '8. Baggage',
      content: `Baggage policies:

• Baggage allowances are set by individual airlines
• Excess baggage fees are payable directly to the airline
• Restricted and prohibited items must not be carried
• We are not liable for lost, damaged, or delayed baggage
• Claims for baggage issues should be filed with the airline

Check your booking confirmation for specific baggage limits. Additional baggage can often be pre-purchased at a lower rate than airport fees.`
    },
    {
      title: '9. Limitation of Liability',
      content: `FlightBooker's liability is limited as follows:

• We act as an intermediary and are not the carrier
• We are not liable for flight delays, cancellations, or schedule changes by airlines
• Our liability for any claim is limited to the booking value
• We are not responsible for indirect, consequential, or incidental damages
• Force majeure events (natural disasters, strikes, etc.) exempt us from liability

Airlines bear responsibility for flight operations. Any claims related to the flight itself should be directed to the operating carrier.`
    },
    {
      title: '10. Privacy and Data Protection',
      content: `We value your privacy:

• Personal information is collected and processed per our Privacy Policy
• We use industry-standard security measures to protect your data
• Your information may be shared with airlines and service providers as necessary
• We do not sell your personal data to third parties
• You can request data access, correction, or deletion

Please review our Privacy Policy for detailed information on how we handle your data.`
    },
    {
      title: '11. Intellectual Property',
      content: `All content on FlightBooker is protected:

• Website design, logos, and graphics are our intellectual property
• Content may not be copied, reproduced, or distributed without permission
• User-generated content grants us a non-exclusive license to use it
• Trademarks of airlines and partners belong to their respective owners

Unauthorized use of our intellectual property may result in legal action.`
    },
    {
      title: '12. Governing Law and Disputes',
      content: `Legal framework:

• These terms are governed by the laws of India
• Courts in New Delhi shall have exclusive jurisdiction
• Disputes will first be addressed through our grievance redressal process
• Mediation will be attempted before litigation
• Consumer protection laws apply where applicable

For any disputes, please first contact our customer support team. Most issues can be resolved amicably.`
    },
    {
      title: '13. Contact Information',
      content: `For questions about these terms:

• Email: legal@flightbooker.com
• Phone: 1800-XXX-XXXX
• Address: Tech Park, Sector 126, Noida, UP 201303, India

Our customer support team is available 24/7 to assist with any queries.`
    }
  ];

  return (
    <>
      <Navbar />
      <div className="static-page terms-page">
        <div className="static-hero">
          <div className="hero-content">
            <FileText size={48} />
            <h1>Terms & Conditions</h1>
            <p>Please read these terms carefully before using our services</p>
          </div>
        </div>

        <div className="static-container">
          <div className="legal-meta">
            <p><strong>Last Updated:</strong> {lastUpdated}</p>
            <p><strong>Effective Date:</strong> {lastUpdated}</p>
          </div>

          <div className="legal-intro">
            <p>
              Welcome to FlightBooker. These Terms and Conditions ("Terms") govern your use of our 
              website, mobile applications, and services (collectively, the "Platform"). By using 
              our Platform, you agree to these Terms in their entirety.
            </p>
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
              By using FlightBooker's services, you acknowledge that you have read, understood, 
              and agree to be bound by these Terms and Conditions. If you have any questions, 
              please contact us at legal@flightbooker.com.
            </p>
          </div>
        </div>
      </div>
      <Footer />
    </>
  );
};

export default TermsPage;
