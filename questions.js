// ================================================================================
// SPEAKING MOCK TEST - QUESTIONS DATA
// ================================================================================
// This file contains all question content for the Speaking Mock Test
// Update this file to change questions across all 9 sections automatically
// ================================================================================

const SPEAKING_TEST_DATA = {
  // Images for Q4, Q5, Q6 (all three questions share the same 2 images)
  images: {
    img1: 'https://i.ibb.co/SDwRVyw8/image.png',
    img2: 'https://i.ibb.co/rT8fKFs/image.png',
    img1Alt: 'Festival event',
    img2Alt: 'Museum visit'
  },

  // Questions 1-8 with all required data
  questions: [
    // Q1
    {
      number: 1,
      part: 'Part 1',
      badge: '30s',
      prepTime: 5,
      speakTime: 30,
      prompt: "What is the best movie you've ever seen?",
      sampleAnswer: "I think the best book I've <span class=\"ml-token adv\">ever</span> read is <span class=\"ml-token colloc\">To Kill a Mockingbird</span> by Harper Lee. It's a classic, and <span class=\"ml-token adv\">honestly</span>, it <span class=\"ml-token adv\">really</span> opened my eyes to issues like justice, racism, and empathy. The way the story unfolds through the eyes of a young girl is <span class=\"ml-token adv\">incredibly</span> powerful. I <span class=\"ml-token phrasal\">picked it up</span> in high school and couldn't <span class=\"ml-token phrasal\">put it down</span>. What I love most is how the characters feel so real — you <span class=\"ml-token adv\">genuinely</span> care about them. <span class=\"ml-token adv\">Plus</span>, it taught me that <span class=\"ml-token proverb\">\"standing up for what's right isn't always easy, but it's always worth it.\"</span> It's one of those books that stays with you long after you've finished reading.",
      vocabulary: {
        title: "Q1 - Best book you've ever read",
        sentenceStarters: [
          '"Yes, we have quite a collection..." - "Ha, bizda ancha ko\'p kitoblar bor..."',
          '"We\'ve got several shelves full of..." - "Bir necha javon to\'la ... bor"',
          '"My parents/family members are big readers, so..." - "Ota-onam/oila a\'zolarim ko\'p o\'qiydi, shuning uchun..."'
        ],
        phrases: [
          '<strong>quite a collection</strong> - "ancha katta to\'plam"',
          '<strong>classics, novels, textbooks</strong> - "klassik asarlar, romanlar, darsliklar"',
          '<strong>to flip through a book</strong> - "kitobni varaqlash"',
          '<strong>to pick up (buy/get)</strong> - "sotib olmoq / olmoq"',
          '<strong>to throw books away</strong> - "kitoblarni tashlash"',
          '<strong>work on vocabulary</strong> - "so\'z boyligini oshirish"'
        ],
        idioms: [
          '<strong>big reader</strong> - "ko\'p o\'qiydigan odam"',
          '"A room without books is like a body without a soul." - "Kitobsiz xona - rухsiz tanga o\'xshaydi."',
          '"Books are a uniquely portable magic." - "Kitoblar - ko\'chma sehr."'
        ]
      }
    },


    // Q2
    {
      number: 2,
      part: 'Part 1',
      badge: '30s',
      prepTime: 5,
      speakTime: 30,
      prompt: 'Would you want to be an actor in the future?',
      sampleAnswer: "<span class=\"ml-token adv\">Honestly</span>, I'm not sure. On one hand, being an actor sounds <span class=\"ml-token adv\">incredibly</span> exciting — you get to <span class=\"ml-token phrasal\">step into</span> different characters, tell stories, and connect with audiences. <span class=\"ml-token adv\">Plus</span>, the idea of performing on stage or in films is <span class=\"ml-token adv\">really</span> appealing. But on the other hand, it's such a competitive and unpredictable field. You have to deal with rejection, long hours, and constant public attention. I think I'd enjoy acting as a hobby, like joining a local theater group, but <span class=\"ml-token colloc\">making it my career</span> feels too risky. I prefer something more stable where I can still be creative but with <span class=\"ml-token colloc\">less pressure</span>. As they say, <span class=\"ml-token proverb\">\"Don't put all your eggs in one basket.\"</span>",
      vocabulary: {
        title: 'Q2 - Would you want to be an actor?',
        sentenceStarters: [
          '"Yes, I\'m really into..." - "Ha, men juda yoqtiraman..."',
          '"I listen to a few international artists, like..." - "Men bir necha xorijiy artistlarni tinglayman, masalan..."',
          '"I enjoy their music because..." - "Ularning musiqasini yoqtiraman, chunki..."'
        ],
        phrases: [
          '<strong>super catchy songs</strong> - "juda yoqimli/esda qoladigan qo\'shiqlar"',
          '<strong>to look up the lyrics</strong> - "so\'zlarini qidirmoq/topmoq"',
          '<strong>to pick up expressions</strong> - "iboralarni o\'rganib olmoq"',
          '<strong>well-produced music videos</strong> - "yaxshi tayyorlangan video kliplar"',
          '<strong>the whole vibe</strong> - "butun atmosfera/kayfiyat"'
        ],
        idioms: [
          '"Music is the universal language." - "Musiqa - umumbashariy til."',
          '<strong>to be into something</strong> - "biror narsani juda yoqtirmoq"',
          '"Where words fail, music speaks." - "So\'zlar yetmasa, musiqa gapiradi."'
        ]
      }
    },




    // Q3
    {
      number: 3,
      part: 'Part 1',
      badge: '30s',
      prepTime: 5,
      speakTime: 30,
      prompt: 'Where do you usually buy your clothes?',
      sampleAnswer: "I <span class=\"ml-token adv\">usually</span> shop at a mix of places. For everyday stuff like t-shirts or jeans, I go to <span class=\"ml-token colloc\">high-street stores</span> or shopping malls because they're affordable and have a good variety. But <span class=\"ml-token adv\">occasionally</span>, I <span class=\"ml-token phrasal\">browse through</span> online stores too — it's <span class=\"ml-token adv\">super</span> convenient, and you can <span class=\"ml-token phrasal\">pick up</span> some great deals during sales. I'm not <span class=\"ml-token adv\">really</span> into luxury brands; I prefer clothes that are comfortable and functional rather than flashy. <span class=\"ml-token adv\">Also</span>, I try to buy from brands that are <span class=\"ml-token colloc\">environmentally conscious</span> when I can because sustainability matters. As they say, <span class=\"ml-token proverb\">\"Quality over quantity,\"</span> so I'd rather have a few good pieces than a wardrobe full of cheap stuff.",
      vocabulary: {
        title: 'Q3 - Where do you buy your clothes?',
        sentenceStarters: [
          '"I mostly buy from..." - "Asosan... dan sotib olaman"',
          '"I like shopping at..." - "Men ... da xarid qilishni yoqtiraman"',
          '"I prefer... because..." - "Men afzal ko\'raman... chunki..."'
        ],
        phrases: [
          '<strong>high-street stores</strong> - "oddiy/ommabop do\'konlar"',
          '<strong>great deals</strong> - "ajoyib takliflar"',
          '<strong>environmentally conscious</strong> - "ekologik ongli"',
          '<strong>quality over quantity</strong> - "sifat miqdordan muhimroq"',
          '<strong>browse through</strong> - "ko\'rib chiqmoq"'
        ],
        idioms: [
          '<strong>window shopping</strong> - "faqat ko\'rish uchun aylanmoq"',
          '"Dress for the job you want, not the job you have."',
          '"Clothes make the man." - "Kiyim odamni yaratadi."'
        ]
      }
    },




    // Q4
    {
      number: 4,
      part: 'Part 1',
      badge: '45s',
      prepTime: 10,
      speakTime: 45,
      prompt: 'What do you see in these pictures?',
      hasImages: true,
      sampleAnswer: "Both pictures show different cultural experiences. In the first picture, I can see what looks like a <span class=\"ml-token colloc\">lively festival</span> — there are <span class=\"ml-token adv\">probably</span> lots of people gathered together, maybe enjoying music, performances, or traditional celebrations. The atmosphere seems energetic and vibrant, with bright colors and a sense of community. Festivals are all about <span class=\"ml-token phrasal\">coming together</span>, celebrating culture, and having fun outdoors.<br><br>In the second picture, there's a museum — <span class=\"ml-token adv\">probably</span> an art or history museum with exhibits on display. The setting feels more quiet and structured. Museums are places where you <span class=\"ml-token phrasal\">slow down</span>, observe artifacts or artwork, and learn about history or creativity. The vibe is calm and educational, unlike the festival's excitement.<br><br>So one picture represents a <span class=\"ml-token colloc\">social cultural event</span> — loud, interactive, full of energy. The other shows a <span class=\"ml-token colloc\">more formal learning environment</span> — peaceful, reflective, focused on knowledge. If I wanted to <span class=\"ml-token phrasal\">let loose</span> and enjoy myself with friends, I'd choose the festival. If I wanted to <span class=\"ml-token phrasal\">broaden my mind</span> and appreciate art or history, I'd visit the museum.",
      vocabulary: {
        title: 'Q4 - What do you see in these pictures?',
        sentenceStarters: [
          '"In the first picture, I can see..." - "Birinchi rasmda... ko\'rish mumkin"',
          '"The second picture shows..." - "Ikkinchi rasm... ko\'rsatadi"',
          '"Both pictures depict..." - "Ikkala rasm ham... tasvirlaydi"'
        ],
        phrases: [
          '<strong>lively festival</strong> - "jonli festival"',
          '<strong>social cultural event</strong> - "ijtimoiy madaniy tadbir"',
          '<strong>coming together</strong> - "birlashmoq"',
          '<strong>formal learning environment</strong> - "rasmiy o\'rganish muhiti"',
          '<strong>let loose</strong> - "dam olmoq/zavqlanmoq"'
        ],
        idioms: [
          '<strong>broaden my mind</strong> - "dunyoqarashni kengaytirish"',
          '"A picture is worth a thousand words."',
          '<strong>slow down</strong> - "sekinlashmoq"'
        ]
      }
    },




    // Q5
    {
      number: 5,
      part: 'Part 1',
      badge: '30s',
      prepTime: 5,
      speakTime: 30,
      prompt: 'What are the advantages of attending a festival compared to a museum visit?',
      hasImages: true,
      sampleAnswer: "I think the main advantage of attending a festival is the <span class=\"ml-token colloc\">social experience</span>. Festivals are <span class=\"ml-token adv\">incredibly</span> lively — you get to <span class=\"ml-token phrasal\">hang out</span> with friends, meet new people, enjoy live performances, and <span class=\"ml-token adv\">really</span> <span class=\"ml-token idiom\">let your hair down</span>. There's this sense of freedom and celebration that you don't get in a museum. <span class=\"ml-token adv\">Also</span>, festivals are <span class=\"ml-token adv\">usually</span> outdoors, so you're in fresh air, moving around, dancing, or trying different foods. It's more interactive and energetic. Museums, on the other hand, are quieter and more solitary — you're <span class=\"ml-token adv\">mostly</span> observing and thinking. So if you want fun, energy, and social connection, festivals are <span class=\"ml-token adv\">definitely</span> the better choice.",
      vocabulary: {
        title: 'Q5 - Advantages of festival vs museum',
        sentenceStarters: [
          '"I think the main advantage is..." - "Asosiy afzallik... deb o\'ylayman"',
          '"Festivals offer..." - "Festivallar... taklif qiladi"',
          '"On the other hand..." - "Boshqa tomondan..."'
        ],
        phrases: [
          '<strong>social experience</strong> - "ijtimoiy tajriba"',
          '<strong>hang out</strong> - "vaqt o\'tkazmoq"',
          '<strong>let your hair down</strong> - "dam olmoq/zavqlanmoq"',
          '<strong>fresh air</strong> - "toza havo"',
          '<strong>interactive and energetic</strong> - "interaktiv va energik"'
        ],
        idioms: [
          '"Live in the moment." - "Hozirgi daqiqada yasha."',
          '<strong>let loose</strong> - "o\'zini bo\'shatmoq"',
          '"Life is a festival."'
        ]
      }
    },




    // Q6
    {
      number: 6,
      part: 'Part 1',
      badge: '30s',
      prepTime: 5,
      speakTime: 30,
      prompt: 'Why might some people find museums boring?',
      hasImages: true,
      sampleAnswer: "I think some people find museums boring because they're <span class=\"ml-token adv\">often</span> quite slow-paced and passive. You're <span class=\"ml-token adv\">mainly</span> just walking around, reading descriptions, and looking at exhibits — it's not as <span class=\"ml-token colloc\">hands-on or interactive</span> as other activities. For people who prefer action, movement, or socializing, museums can feel a bit too quiet and serious. <span class=\"ml-token adv\">Also</span>, if you're not <span class=\"ml-token adv\">particularly</span> interested in art, history, or science, the content might not <span class=\"ml-token phrasal\">resonate with you</span>. Museums require patience and focus, which isn't everyone's style. <span class=\"ml-token adv\">Plus</span>, some museums can be overwhelming with too much information or poorly designed exhibits. So it depends on personal preference — what's fascinating to one person might feel dull to another.",
      vocabulary: {
        title: 'Q6 - Why museums might be boring',
        sentenceStarters: [
          '"Personally, I prefer..." - "Shaxsan men afzal ko\'raman..."',
          '"I know planes are faster, but..." - "Samolyotlar tezroq, lekin..."',
          '"Unless I\'m crossing an ocean, I\'d choose..." - "Okean kesib o\'tmasam, ... tanlar edim"'
        ],
        phrases: [
          '<strong>much more space</strong> - "ancha ko\'proq joy"',
          '<strong>changing scenery</strong> - "o\'zgarib turuvchi manzara"',
          '<strong>staring at clouds</strong> - "bulutlarga qarab o\'tirish"',
          '<strong>baggage restrictions</strong> - "yuk cheklovlari"',
          '<strong>stressful security</strong> - "stressli xavfsizlik tekshiruvi"'
        ],
        idioms: [
          '<strong>locked in a tin can</strong> - "qutida qamalib qolish"',
          '<strong>hands down</strong> - "shubhasiz / aniq"',
          '"The journey is the destination."'
        ]
      }
    },




    // Q7
    {
      number: 7,
      part: 'Part 2',
      badge: '2:00',
      prepTime: 60,
      speakTime: 120,
      prompt: 'Discuss the following points:',
      bulletPoints: [
        'Can you describe a trip that left a lasting impression on you?',
        'What do you think made a trip special?',
        'How does traveling affect one\'s attitude toward life and cultures?'
      ],
      sampleAnswer: "I'd love to talk about traveling. One trip that <span class=\"ml-token adv\">really</span> left a lasting impression on me was when I visited Japan a couple of years ago. It was my first time traveling to Asia, and everything felt so different yet fascinating. What made it special was the combination of tradition and modernity — one moment you're walking through ancient temples in Kyoto, and the next you're in the middle of Tokyo's neon-lit streets. The people were <span class=\"ml-token adv\">incredibly</span> polite and respectful, which <span class=\"ml-token phrasal\">stood out</span> to me. I also loved trying authentic Japanese food, like ramen and sushi, which tasted nothing like what we have back home.<br><br>What makes a trip special, in my opinion, is when you <span class=\"ml-token phrasal\">step out of</span> your comfort zone and experience something completely new. It's not just about sightseeing; it's about <span class=\"ml-token colloc\">immersing yourself</span> in a different culture, meeting locals, and learning their way of life. Traveling teaches you to be more open-minded and adaptable.<br><br>As for how traveling affects one's attitude, I think it broadens your perspective. You start to see the world from different angles and realize that there's no single \"right\" way to live. It makes you more empathetic and appreciative of diversity. As they say, <span class=\"ml-token proverb\">\"Travel is the only thing you buy that makes you richer.\"</span>",
      vocabulary: {
        title: 'Q7 - Travel discussion',
        sentenceStarters: [
          '"One achievement I\'m really proud of is..." - "Juda faxrlanganim yutuqim..."',
          '"That success taught me..." - "Bu muvaffaqiyat menga o\'rgatdi..."',
          '"Success means different things to different people..." - "Muvaffaqiyat har bir kishi uchun boshqa narsa..."'
        ],
        phrases: [
          '<strong>set aside time</strong> - "vaqt ajratmoq"',
          '<strong>pushing through difficulties</strong> - "qiyinchiliklarni yengib o\'tmoq"',
          '<strong>stick with something</strong> - "biror narsa bilan davom etmoq"',
          '<strong>small daily progress</strong> - "har kuni kichik muvaffaqiyat"',
          '<strong>move mountains</strong> - "katta ishlarni qilmoq"',
          '<strong>give up early</strong> - "erta taslim bo\'lmoq"'
        ],
        idioms: [
          '<strong>all over the place</strong> - "tartibsiz / chalg\'igan"',
          '"Success is not the key to happiness. Happiness is the key to success."',
          '"Effort and patience beat natural talent."'
        ]
      }
    },




    // Q8
    {
      number: 8,
      part: 'Part 3 (Discussion)',
      badge: '2:00',
      prepTime: 60,
      speakTime: 120,
      prompt: 'Art classes should be mandatory in schools.',
      promptInstruction: 'Discuss both sides and give your opinion.',
      debatePoints: {
        for: [
          'Encourages creativity and self-expression',
          'Improves problem-solving skills',
          'Provides a break from academic subjects'
        ],
        against: [
          'Not everyone is interested in art',
          'Reduces time for core subjects',
          'Expensive to implement in all schools'
        ]
      },
      sampleAnswer: "This is an interesting topic. Some people argue that art classes should be mandatory in schools, while others disagree. Let me discuss both sides.<br><br>On the one hand, art classes <span class=\"ml-token colloc\">encourage creativity and self-expression</span>. Students get a chance to explore their artistic side, which can be <span class=\"ml-token adv\">really</span> beneficial for their mental and emotional development. Art also <span class=\"ml-token colloc\">improves problem-solving skills</span> because it requires you to think outside the box. <span class=\"ml-token adv\">Plus</span>, it <span class=\"ml-token colloc\">provides a break from academic subjects</span> like math and science, giving students a chance to relax and recharge.<br><br>On the other hand, <span class=\"ml-token colloc\">not everyone is interested in art</span>. For some students, mandatory art classes might feel like a waste of time, especially if they'd rather focus on subjects they're passionate about. <span class=\"ml-token adv\">Also</span>, art classes <span class=\"ml-token colloc\">reduce time for core subjects</span> like English, math, or science, which are essential for exams and careers. <span class=\"ml-token adv\">Finally</span>, implementing art programs can be <span class=\"ml-token colloc\">expensive</span> — schools need to buy materials, hire qualified teachers, and create proper facilities, which not all schools can afford.<br><br>In my opinion, I think art classes should be available but not mandatory. Schools should offer them as electives so students who are interested can take them, while others can focus on what they prefer. This way, everyone benefits without feeling forced into something they don't enjoy. As they say, <span class=\"ml-token proverb\">\"You can't force creativity.\"</span>",
      vocabulary: {
        title: 'Q8 - Art classes should be mandatory in schools',
        sentenceStarters: [
          '"Many people argue that..." - "Ko\'pchilik aytadilarki..."',
          '"On the other hand, some believe..." - "Boshqa tomondan, ba\'zilar ishonadi..."',
          '"In my opinion, higher taxes make sense, but..." - "Menimcha, yuqori soliqlar mantiqiy, lekin..."'
        ],
        phrases: [
          '<strong>struggling to get by</strong> - "kunni kechirish uchun kurashmoq"',
          '<strong>balancing inequality</strong> - "tengsizlikni muvozanatlash"',
          '<strong>basic opportunities</strong> - "asosiy imkoniyatlar"',
          '<strong>give back to society</strong> - "jamiyatga qaytarish"',
          '<strong>lose motivation / push yourself</strong> - "motivatsiyani yo\'qotmoq / o\'zingni undamoq"',
          '<strong>move abroad</strong> - "chet elga ko\'chmoq"',
          '<strong>progressive taxation</strong> - "progressiv soliq tizimi"',
          '<strong>waste tax money</strong> - "soliq pulini isrof qilmoq"'
        ],
        idioms: [
          '"To whom much is given, much is expected." - "Kimga ko\'p berilsa, undan ko\'p kutiladi."',
          '<strong>drive them away</strong> - "ularni haydab yubormoq"',
          '"Taxation should be about fairness, not punishment."'
        ]
      }
    }
  ]
};

// Make it available globally
if (typeof window !== 'undefined') {
  window.SPEAKING_TEST_DATA = SPEAKING_TEST_DATA;
}