// A principal reviewing proposed topics saw "template:ncert-textbook-contents"
// as their source: only two of the server's template names had words.
import 'package:flutter_test/flutter_test.dart';

import 'package:academicos/data/datasources/api/curriculum_api.dart';

ChapterTopicProposals _from(String provenance) =>
    ChapterTopicProposals(runId: 'r', status: 'pending', provenance: provenance, topics: const []);

void main() {
  test('every template the server proposes from is named in words', () {
    for (final p in ['template:school_1-approved', 'template:ncert-textbook-headings',
        'template:ncert-textbook-contents', 'template:ncert-book-chapter']) {
      expect(_from(p).sourceLabel, isNot(startsWith('template:')), reason: p);
    }
    expect(_from('template:ncert-book-chapter').sourceLabel, contains('does not divide it'));
    expect(_from('llm-v3').sourceLabel, 'an AI draft');
  });
}
